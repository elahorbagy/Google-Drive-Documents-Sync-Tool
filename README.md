# Google Drive Documents Sync Tool

An automated Python tool designed to synchronize and upload local documents from your computer's `Documents` folder (e.g. `C:\Documents` or `C:\Users\<User>\Documents`) to a dedicated `Documents` folder on **Google Drive** through your web browser.

---

## Key Features

- **Automatic Local Path Discovery**: Automatically detects `C:\Documents` or your active Windows user profile's `Documents` directory without hardcoded paths.
- **Dual Connection Modes**:
  - **Direct Browser Automation (`--mode browser`)**: Uses Playwright to open a real Chromium session. Log into Google once, and the tool saves your session to upload files directly through Google Drive's web interface without requiring a Google Cloud project or `credentials.json`.
  - **Official Google Drive API (`--mode api`)**: Uses OAuth 2.0 flow to launch your browser once for authorization, then mirrors entire directory structures and subfolders at high speed in the background.
- **Silent Background Operation (`--headless`)**: Runs browser automation invisibly in the background without opening popups once authenticated.
- **Smart Duplicate Prevention**: Computes local MD5 checksums and compares them against remote files to skip unchanged files and save bandwidth.
- **Automatic File Filtering (`--exclude`)**: Automatically ignores temporary Microsoft Office lock files (`~$*`), cache files (`*.tmp`), system artifacts (`desktop.ini`, `Thumbs.db`), and Git repositories (`.git`).
- **Activity & Error Logging**: Writes complete execution logs with human-readable file sizes and duration stats to `sync.log`.
- **Continuous Watch Mode (`--watch`)**: Runs silently in the background, monitoring your folder and automatically uploading any new or modified files.

---

## Requirements & Installation

Clone or download this repository, then install the dependencies for your chosen mode:

### Option A: Direct Browser Automation (Recommended & Simplest)
No Google Cloud setup required:
```bash
pip install playwright
playwright install chromium
```

### Option B: Official Google Drive API Mode
Requires a `credentials.json` OAuth 2.0 Desktop client from Google Cloud Console placed in the same folder:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

*Or install everything at once:*
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Quick Start

### 1. Run via Direct Browser Automation
```bash
python gdrive_documents_sync.py --mode browser
```
*On your first run, a browser window will open to let you sign into your Google account. Your session is saved locally in `gdrive_browser_profile/` so subsequent runs will proceed automatically.*

### 2. Run Silently in the Background (Headless)
```bash
python gdrive_documents_sync.py --mode browser --headless
```

### 3. Run via Google Drive API
```bash
python gdrive_documents_sync.py --mode api
```

### 4. Continuous Watch & Auto-Sync
Keep the script running in the background to automatically upload any newly added or updated files every 60 seconds:
```bash
python gdrive_documents_sync.py --mode browser --headless --watch --interval 60
```

---

## CLI Options & Flags

```text
usage: gdrive_documents_sync.py [-h] [--source SOURCE]
                                [--remote-folder REMOTE_FOLDER]
                                [--mode {auto,browser,api}] [--headless]
                                [--exclude [EXCLUDE ...]] [--watch]
                                [--interval INTERVAL] [--verbose]

options:
  -h, --help            Show this help message and exit
  --source SOURCE       Custom local folder path (default: auto-detects C:\Documents)
  --remote-folder REMOTE_FOLDER
                        Target folder name on Google Drive (default: Documents)
  --mode {auto,browser,api}
                        Connection mode (default: auto)
  --headless            Run browser automation without opening a visible UI
  --exclude [EXCLUDE ...]
                        Custom file patterns to ignore (e.g. *.iso *.zip)
  --watch               Enable continuous polling to upload modified or new files
  --interval INTERVAL   Polling interval in seconds when --watch is enabled (default: 60)
  --verbose             Enable detailed debug console logs
```

---

## Building a Standalone Windows Executable (.exe)

You can compile this tool into a standalone `.exe` so it runs without installing Python:

```bash
pip install pyinstaller
pyinstaller --onefile --name "GDriveSync" gdrive_documents_sync.py
```
Your executable will be created inside the `dist/` folder.

---

## License

This project is licensed under the MIT License.
