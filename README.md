# Google Drive Documents Sync Tool

An automated Python tool designed to synchronize and upload local documents from your computer's `Documents` folder (e.g. `C:\Documents` or `C:\Users\<User>\Documents`) to a dedicated `Documents` folder on **Google Drive** through your web browser.

---

## Key Features

- **Automatic Local Path Discovery**: Automatically detects `C:\Documents` or your active Windows user profile's `Documents` directory without hardcoded paths.
- **Dual Connection Modes**:
  - **Direct Browser Automation (`--mode browser`)**: Uses Playwright to open a real Chromium session. Log into Google once, and the tool saves your session to upload files directly through Google Drive's web interface without requiring a Google Cloud project or `credentials.json`.
  - **Official Google Drive API (`--mode api`)**: Uses OAuth 2.0 flow to launch your browser once for authorization, then mirrors entire directory structures and subfolders at high speed in the background.
- **Smart Duplicate Prevention**: Computes local MD5 checksums and compares them against remote files to skip unchanged files and save bandwidth.
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

---

## Quick Start

### 1. Run via Direct Browser Automation
```bash
python gdrive_documents_sync.py --mode browser
```
*On your first run, a browser window will open to let you sign into your Google account. Your session is saved locally in `gdrive_browser_profile/` so subsequent runs will proceed automatically.*

### 2. Run via Google Drive API
```bash
python gdrive_documents_sync.py --mode api
```

### 3. Continuous Watch & Auto-Sync
Keep the script running in the background to automatically upload any newly added or updated files every 60 seconds:
```bash
python gdrive_documents_sync.py --mode browser --watch
```

---

## CLI Options & Flags

```text
usage: gdrive_documents_sync.py [-h] [--source SOURCE]
                                [--remote-folder REMOTE_FOLDER]
                                [--mode {auto,browser,api}] [--watch]
                                [--interval INTERVAL]

options:
  -h, --help            Show this help message and exit
  --source SOURCE       Custom local folder path (default: auto-detects C:\Documents)
  --remote-folder REMOTE_FOLDER
                        Target folder name on Google Drive (default: Documents)
  --mode {auto,browser,api}
                        Connection mode (default: auto)
  --watch               Enable continuous polling to upload modified or new files
  --interval INTERVAL   Polling interval in seconds when --watch is enabled (default: 60)
```

---

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).
