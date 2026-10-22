#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Drive Documents Folder Uploader & Sync Tool (Enhanced Edition)

Created: 2026
Description:
An enterprise-grade, automated tool that detects your local Documents folder
(C:\\Documents or C:\\Users\\<User>\\Documents), connects to Google Drive via
browser automation (Playwright) or Google Drive API (OAuth2), and mirrors
all your files and directories into a dedicated 'Documents' folder on Google Drive.

Key Enhancements in this Version:
- Integrated file logging (sync.log) and rich console reporting.
- Smart file filtering (skips lock files like ~$*, *.tmp, desktop.ini, .git).
- Headless browser toggle (--headless) for background silent operation.
- Human-readable file sizes and upload duration metrics.
- Seamless MD5 checksum tracking to avoid duplicate uploads.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import logging
import mimetypes
import os
import pathlib
import sys
import time
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# Configuration & Constants
# ==============================================================================

DEFAULT_REMOTE_FOLDER_NAME = "Documents"
STATE_FILE_NAME = ".gdrive_sync_state.json"
LOG_FILE_NAME = "sync.log"

DEFAULT_IGNORE_PATTERNS = [
    "~$*",               # Microsoft Office lock files
    "*.tmp",             # Temporary files
    "*.crdownload",      # Incomplete browser downloads
    "desktop.ini",       # Windows shell config
    "Thumbs.db",         # Windows thumbnail cache
    ".DS_Store",         # macOS directory artifacts
    ".git*",             # Git metadata
    "__pycache__",       # Python cache
    "*.pyc",
    STATE_FILE_NAME,
    LOG_FILE_NAME,
    "gdrive_browser_profile",
    "token.json",
    "credentials.json",
]


# ==============================================================================
# Logging Setup
# ==============================================================================

def setup_logger(log_file: pathlib.Path, verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("GDriveSync")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    # Formatter
    file_fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

    # File handler
    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_fmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)

    return logger


# ==============================================================================
# Utility Functions
# ==============================================================================

def format_size(bytes_num: int) -> str:
    """Returns human-readable file size string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


def compute_file_md5(file_path: pathlib.Path) -> str:
    """Computes MD5 hash in chunks to prevent memory spikes on large files."""
    hasher = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def should_ignore(path: pathlib.Path, custom_patterns: Optional[List[str]] = None) -> bool:
    """Checks if a file or directory matches any ignore pattern."""
    patterns = DEFAULT_IGNORE_PATTERNS + (custom_patterns or [])
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def resolve_local_documents_dir(custom_path: Optional[str] = None) -> pathlib.Path:
    """
    Detects the local Documents folder on the C: drive.
    Checks custom path first, then C:\\Documents, then user profile Documents.
    """
    if custom_path:
        p = pathlib.Path(custom_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Custom directory does not exist: {p}")
        return p

    candidates = [
        pathlib.Path("C:/Documents"),
        pathlib.Path.home() / "Documents",
        pathlib.Path("C:/Users") / os.environ.get("USERNAME", "") / "Documents",
    ]

    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()
        except OSError:
            continue

    fallback = pathlib.Path("C:/Documents") if os.name == "nt" else (pathlib.Path.home() / "Documents")
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback.resolve()


# ==============================================================================
# Mode 1: Google Drive OAuth2 API
# ==============================================================================

class GoogleDriveOAuthUploader:
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    def __init__(
        self,
        credentials_path: pathlib.Path,
        token_path: pathlib.Path,
        logger: logging.Logger,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.logger = logger
        self.service = self._authenticate_via_browser()

    def _authenticate_via_browser(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            self.logger.error("Missing Google Drive API packages.")
            print(
                "[!] Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
            raise SystemExit(1) from exc

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired Google Drive session token...")
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    self.logger.error("OAuth credentials.json not found.")
                    print(
                        f"[!] Please place '{self.credentials_path.name}' in the project folder, OR\n"
                        "    run in browser mode: python gdrive_documents_sync.py --mode browser"
                    )
                    raise SystemExit(1)

                self.logger.info("Opening browser to authorize Google Drive access...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=True)

            self.token_path.write_text(creds.to_json(), encoding="utf-8")
            self.logger.info("Authentication token successfully saved.")

        return build("drive", "v3", credentials=creds)

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        escaped_name = folder_name.replace("'", "\\'")
        query_parts = [
            f"name = '{escaped_name}'",
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")
        else:
            query_parts.append("'root' in parents")

        query = " and ".join(query_parts)
        response = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        files = response.get("files", [])
        if files:
            return files[0]["id"]

        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        folder = self.service.files().create(body=metadata, fields="id").execute()
        self.logger.info(f"Created remote folder: {folder_name}")
        return folder["id"]

    def upload_or_update_file(self, local_file: pathlib.Path, parent_folder_id: str) -> None:
        from googleapiclient.http import MediaFileUpload

        escaped_name = local_file.name.replace("'", "\\'")
        query = (
            f"name = '{escaped_name}' and "
            f"'{parent_folder_id}' in parents and "
            "trashed = false"
        )
        response = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name, md5Checksum)", pageSize=1)
            .execute()
        )
        existing_files = response.get("files", [])
        local_md5 = compute_file_md5(local_file)
        file_size = format_size(local_file.stat().st_size)

        mime_type, _ = mimetypes.guess_type(str(local_file))
        if not mime_type:
            mime_type = "application/octet-stream"

        media = MediaFileUpload(str(local_file), mimetype=mime_type, resumable=True)

        if existing_files:
            remote_file = existing_files[0]
            if remote_file.get("md5Checksum") == local_md5:
                self.logger.debug(f"[=] Up-to-date: {local_file.name}")
                return

            self.logger.info(f"[~] Updating {local_file.name} ({file_size})...")
            start_t = time.time()
            self.service.files().update(fileId=remote_file["id"], media_body=media).execute()
            self.logger.info(f"[✓] Updated {local_file.name} in {time.time()-start_t:.1f}s")
        else:
            self.logger.info(f"[↑] Uploading {local_file.name} ({file_size})...")
            start_t = time.time()
            metadata = {"name": local_file.name, "parents": [parent_folder_id]}
            self.service.files().create(body=metadata, media_body=media, fields="id").execute()
            self.logger.info(f"[✓] Uploaded {local_file.name} in {time.time()-start_t:.1f}s")

    def sync_directory_tree(
        self,
        local_root: pathlib.Path,
        remote_root_name: str,
        custom_ignores: Optional[List[str]] = None,
    ) -> None:
        root_folder_id = self.get_or_create_folder(remote_root_name, parent_id=None)
        folder_id_map: Dict[pathlib.Path, str] = {local_root: root_folder_id}

        for current_dir, dirs, files in os.walk(local_root):
            current_path = pathlib.Path(current_dir)
            # Filter directories
            dirs[:] = [
                d for d in dirs
                if not should_ignore(current_path / d, custom_ignores)
            ]

            parent_remote_id = folder_id_map[current_path]

            for d in dirs:
                sub_path = current_path / d
                sub_remote_id = self.get_or_create_folder(d, parent_id=parent_remote_id)
                folder_id_map[sub_path] = sub_remote_id

            for filename in files:
                file_path = current_path / filename
                if should_ignore(file_path, custom_ignores):
                    continue
                try:
                    self.upload_or_update_file(file_path, parent_remote_id)
                except Exception as err:
                    self.logger.error(f"Failed to upload {file_path.name}: {err}")


# ==============================================================================
# Mode 2: Direct Playwright Browser Automation
# ==============================================================================

class BrowserAutomationDriveUploader:
    def __init__(
        self,
        profile_dir: pathlib.Path,
        state_file: pathlib.Path,
        logger: logging.Logger,
        headless: bool = False,
    ) -> None:
        self.profile_dir = profile_dir
        self.state_file = state_file
        self.logger = logger
        self.headless = headless
        self.uploaded_hashes: Dict[str, str] = self._load_state()

    def _load_state(self) -> Dict[str, str]:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_state(self) -> None:
        self.state_file.write_text(
            json.dumps(self.uploaded_hashes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def sync_via_browser(
        self,
        local_root: pathlib.Path,
        remote_folder_name: str,
        custom_ignores: Optional[List[str]] = None,
    ) -> None:
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError as exc:
            self.logger.error("Playwright is not installed.")
            print("[!] Run: pip install playwright && playwright install chromium")
            raise SystemExit(1) from exc

        # Scan for changed/new files
        files_to_upload: List[Tuple[pathlib.Path, str, str, str]] = []
        for current_dir, dirs, files in os.walk(local_root):
            current_path = pathlib.Path(current_dir)
            dirs[:] = [
                d for d in dirs
                if not should_ignore(current_path / d, custom_ignores)
            ]
            for filename in files:
                fp = current_path / filename
                if should_ignore(fp, custom_ignores):
                    continue
                try:
                    f_hash = compute_file_md5(fp)
                    rel_key = str(fp.relative_to(local_root))
                    if self.uploaded_hashes.get(rel_key) != f_hash:
                        f_size = format_size(fp.stat().st_size)
                        files_to_upload.append((fp, rel_key, f_hash, f_size))
                except OSError:
                    continue

        if not files_to_upload:
            self.logger.info("[✓] All files in Documents are synced and up-to-date!")
            return

        self.logger.info(f"[*] Found {len(files_to_upload)} file(s) ready to upload.")
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            # Check if this profile has run before. If not and headless was requested, warn user.
            is_first_run = not (self.profile_dir / "Default").exists()
            actual_headless = self.headless
            if is_first_run and self.headless:
                self.logger.warning(
                    "[!] First run requires interactive Google sign-in. Launching with UI visible..."
                )
                actual_headless = False

            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=actual_headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://drive.google.com/drive/my-drive", wait_until="domcontentloaded")

            if not actual_headless and is_first_run:
                self.logger.info(
                    "[*] Please complete your Google account sign-in in the browser window..."
                )

            new_button_selector = (
                "button[guidedhelpid='new_menu_button'], "
                "button:has-text('New'), "
                "button:has-text('جديد')"
            )
            page.wait_for_selector(new_button_selector, timeout=300_000)
            self.logger.info("[+] Successfully connected to Google Drive!")
            time.sleep(2)

            # Locate or create remote Documents folder
            folder_locator = page.locator(
                f"div[role='gridcell'] div[data-tooltip*='{remote_folder_name}'], "
                f"div[role='row']:has-text('{remote_folder_name}')"
            ).first

            if folder_locator.count() == 0:
                self.logger.info(f"[*] Creating target folder '{remote_folder_name}'...")
                page.locator(new_button_selector).first.click()
                time.sleep(1)
                new_folder_item = page.locator(
                    "div[role='menuitem']:has-text('New folder'), "
                    "div[role='menuitem']:has-text('مجلد جديد')"
                ).first
                new_folder_item.click()
                time.sleep(1)
                input_box = page.locator("input[type='text']").last
                input_box.fill(remote_folder_name)
                page.keyboard.press("Enter")
                time.sleep(3)

            # Open folder
            self.logger.info(f"[*] Navigating into folder '{remote_folder_name}'...")
            target_folder = page.locator(
                f"div[role='row']:has-text('{remote_folder_name}'), "
                f"div[data-tooltip*='{remote_folder_name}']"
            ).first
            target_folder.dblclick()
            time.sleep(3)

            # Upload items
            for idx, (file_path, rel_key, file_hash, file_size) in enumerate(files_to_upload, 1):
                try:
                    self.logger.info(
                        f"[{idx}/{len(files_to_upload)}] Uploading {rel_key} ({file_size})..."
                    )
                    start_t = time.time()
                    with page.expect_file_chooser(timeout=20_000) as fc_info:
                        page.locator(new_button_selector).first.click()
                        time.sleep(1)
                        upload_item = page.locator(
                            "div[role='menuitem']:has-text('File upload'), "
                            "div[role='menuitem']:has-text('تحميل ملف')"
                        ).first
                        upload_item.click()

                    fc = fc_info.value
                    fc.set_files(str(file_path))

                    # Allow time for upload to initiate/stream
                    time.sleep(4)
                    self.uploaded_hashes[rel_key] = file_hash
                    self._save_state()
                    self.logger.info(f"[✓] {rel_key} completed in {time.time()-start_t:.1f}s")
                except PlaywrightTimeoutError:
                    self.logger.error(f"[!] Upload dialog timed out for {rel_key}")
                except Exception as err:
                    self.logger.error(f"[!] Error uploading {rel_key}: {err}")

            time.sleep(5)
            context.close()
            self.logger.info("[✓] All files processed successfully.")


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enterprise-grade Google Drive Documents Folder Uploader & Sync Tool."
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Local Documents folder path (default: auto-detects C:\\Documents or Windows profile)",
    )
    parser.add_argument(
        "--remote-folder",
        type=str,
        default=DEFAULT_REMOTE_FOLDER_NAME,
        help="Target folder name on Google Drive (default: Documents)",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "browser", "api"],
        default="auto",
        help="Sync mode: 'browser' (Playwright), 'api' (OAuth2 API), or 'auto'",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser automation in headless (invisible background) mode",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional glob patterns to ignore (e.g. *.iso *.zip)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor and sync newly created or modified files",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds for --watch mode (default: 60)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug logs",
    )
    return parser.parse_args()


def run_sync_cycle(
    local_dir: pathlib.Path,
    remote_folder: str,
    mode: str,
    script_dir: pathlib.Path,
    logger: logging.Logger,
    headless: bool = False,
    custom_ignores: Optional[List[str]] = None,
) -> None:
    credentials_file = script_dir / "credentials.json"
    token_file = script_dir / "token.json"

    chosen_mode = mode
    if chosen_mode == "auto":
        chosen_mode = "api" if credentials_file.exists() else "browser"

    logger.info("=" * 60)
    logger.info(f"Local Source        : {local_dir}")
    logger.info(f"Target Remote Folder: {remote_folder}")
    logger.info(f"Operational Mode    : {chosen_mode.upper()}")
    logger.info("=" * 60)

    if chosen_mode == "api":
        uploader = GoogleDriveOAuthUploader(
            credentials_path=credentials_file,
            token_path=token_file,
            logger=logger,
        )
        uploader.sync_directory_tree(local_dir, remote_folder, custom_ignores)
    else:
        profile_dir = script_dir / "gdrive_browser_profile"
        state_file = local_dir / STATE_FILE_NAME
        browser_uploader = BrowserAutomationDriveUploader(
            profile_dir=profile_dir,
            state_file=state_file,
            logger=logger,
            headless=headless,
        )
        browser_uploader.sync_via_browser(local_dir, remote_folder, custom_ignores)


def main() -> None:
    args = parse_args()
    script_dir = pathlib.Path(__file__).resolve().parent
    log_file = script_dir / LOG_FILE_NAME
    logger = setup_logger(log_file, args.verbose)

    try:
        local_dir = resolve_local_documents_dir(args.source)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not args.watch:
        run_sync_cycle(
            local_dir=local_dir,
            remote_folder=args.remote_folder,
            mode=args.mode,
            script_dir=script_dir,
            logger=logger,
            headless=args.headless,
            custom_ignores=args.exclude,
        )
        return

    logger.info(f"[*] Continuous watch active every {args.interval}s (Ctrl+C to quit)...")
    try:
        while True:
            run_sync_cycle(
                local_dir=local_dir,
                remote_folder=args.remote_folder,
                mode=args.mode,
                script_dir=script_dir,
                logger=logger,
                headless=args.headless,
                custom_ignores=args.exclude,
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("[!] Watch mode safely terminated by user.")


if __name__ == "__main__":
    main()