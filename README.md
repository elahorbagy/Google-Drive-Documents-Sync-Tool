<div align="center">

# ☁️ Google Drive Documents Sync Tool

**A Dual-Engine Python CLI Utility for Automated Local-to-Cloud Document Synchronization**

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![Google Drive API](https://img.shields.io/badge/Google_Drive-API_v3-4285F4?style=for-the-badge&logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-F5F2EB?style=for-the-badge&labelColor=2C2A29&color=D6CFC2)](LICENSE)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-sync-engines-comparison">Sync Engines</a> •
  <a href="#-installation--setup">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-cli-reference">CLI Reference</a> •
  <a href="#-standalone-executable-exe">Build .EXE</a>
</p>

</div>

---

## 📖 Overview

**Google Drive Documents Sync Tool** is an automated Python utility built to synchronize and back up your local Windows `Documents` directory (`C:\Documents` or `C:\Users\<User>\Documents`) directly to a dedicated folder on **Google Drive**. 

Unlike standard sync scripts that force complex Google Cloud Console configurations, this tool features a **Hybrid Dual-Engine Architecture**—allowing you to either sync zero-config via an automated persistent Chromium browser session or leverage high-speed background directory mirroring through the official Google Drive REST API.

---

## ✨ Key Features

* 🔍 **Zero-Config Path Discovery:** Automatically detects `C:\Documents` or resolves the active Windows user profile directory without hardcoded paths.
* ⚡ **Dual Connection Modes:**
  * **Direct Browser Automation (`--mode browser`):** Powered by Playwright. Sign into Google once to save a persistent session (`gdrive_browser_profile/`) and upload files directly through the web interface—no `credentials.json` or Cloud Console project needed.
  * **Official Google Drive API (`--mode api`):** Uses OAuth 2.0 to authorize once and mirror complex folder hierarchies at high speed in the background.
* 👻 **Silent Headless Execution (`--headless`):** Runs browser automation completely invisibly in the background after initial sign-in.
* 🛡️ **MD5 Checksum Deduplication:** Computes local MD5 hashes and compares them against remote metadata to skip unchanged files and conserve bandwidth.
* 🧹 **Smart Artifact Filtering (`--exclude`):** Automatically ignores temporary Office lock files (`~$*`), temporary caches (`*.tmp`), OS metadata (`desktop.ini`, `Thumbs.db`), and `.git` directories.
* 🔄 **Continuous Watch Daemon (`--watch`):** Polls your directory at customizable intervals to detect and upload newly created or modified files in real time.
* 📊 **Structured Activity Logging:** Records detailed execution metrics, human-readable file sizes, and sync durations to `sync.log`.

---

## ⚖️ Sync Engines Comparison

| Feature | 🌐 Browser Mode (`--mode browser`) | ⚙️ API Mode (`--mode api`) |
| :--- | :--- | :--- |
| **Google Cloud Setup** | ❌ Not Required (Zero-Config) | ✅ Requires `credentials.json` |
| **Authentication** | Interactive Browser Login (Saved Locally) | OAuth 2.0 Token Flow |
| **Background Execution** | ✅ Supported via `--headless` | ✅ Native Background Execution |
| **Best Used For** | Quick setup, personal machines, zero API limits | Large nested directories, high-speed syncing |
| **Est. Download / Bandwidth** | ~130–150 MB *(Playwright + Chromium binary)* | ~15–25 MB *(Lightweight Python libraries)* |

---

## 🛠️ Installation & Setup

Clone the repository and navigate to the project directory:

```bash
git clone [https://github.com/your-username/gdrive-documents-sync.git](https://github.com/your-username/gdrive-documents-sync.git)
cd gdrive-documents-sync
```

Choose your preferred installation method below:

<details open>
<summary><b>Option A: Direct Browser Automation (Recommended & Simplest)</b></summary>
<br>

Requires no Google Cloud setup. Installs Playwright and the standalone Chromium binary *(Est. download: ~150 MB)*:

```bash
pip install playwright
playwright install chromium
```
</details>

<details>
<summary><b>Option B: Official Google Drive API Mode</b></summary>
<br>

Requires a `credentials.json` OAuth 2.0 Desktop Client file placed in the project root *(Est. download: ~20 MB)*:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
</details>

<details>
<summary><b>Option C: Complete Installation (Both Engines)</b></summary>
<br>

Install all dependencies at once *(Est. download: ~170 MB)*:

```bash
pip install -r requirements.txt
playwright install chromium
```
</details>

---

## 🚀 Quick Start

### 1. First-Time Browser Sync (Interactive Auth)
Launch the tool in browser mode. On the first run, a Chromium window will open for you to sign into your Google account. Your session is automatically saved in `gdrive_browser_profile/` for future runs.
```bash
python gdrive_documents_sync.py --mode browser
```

### 2. Silent Background Sync (Headless Mode)
Once authenticated, run the sync invisibly in the background with zero UI popups:
```bash
python gdrive_documents_sync.py --mode browser --headless
```

### 3. High-Speed Sync via Google Drive API
```bash
python gdrive_documents_sync.py --mode api
```

### 4. Continuous Watch & Real-Time Auto-Sync
Keep the daemon running in the background to check for new or modified files every 60 seconds:
```bash
python gdrive_documents_sync.py --mode browser --headless --watch --interval 60
```

### 5. Custom Source Folder & Exclusion Rules
Sync a specific directory while excluding large archives and disk images:
```bash
python gdrive_documents_sync.py --source "D:\Work\Reports" --remote-folder "Work_Backup" --exclude *.iso *.zip *.rar
```

---

## 💻 CLI Reference

| Flag / Argument | Default | Description |
| :--- | :--- | :--- |
| `-h`, `--help` | — | Show the help message and exit. |
| `--source SOURCE` | `Auto-Detected` | Custom local folder path (defaults to `C:\Documents` or User Documents). |
| `--remote-folder NAME` | `Documents` | Target destination folder name on Google Drive. |
| `--mode {auto,browser,api}` | `auto` | Connection engine selection (`auto` falls back gracefully). |
| `--headless` | `False` | Run browser automation invisibly without opening a visible window. |
| `--exclude [PATTERN ...]` | Built-in rules | Space-separated glob patterns to ignore (e.g., `*.iso *.zip`). |
| `--watch` | `False` | Enable continuous background polling for new/updated files. |
| `--interval SECONDS` | `60` | Polling frequency in seconds when `--watch` is active. |
| `--verbose` | `False` | Enable detailed debug output in the console. |

---

## 📦 Standalone Executable (.exe)

You can compile the script into a standalone Windows executable (`.exe`) so it runs on any Windows machine without requiring a Python installation *(Est. package size: ~35–50 MB)*:

```bash
pip install pyinstaller
pyinstaller --onefile --name "GDriveSync" gdrive_documents_sync.py
```

Once compiled, your standalone executable will be ready inside the `dist/` directory:
```bash
.\dist\GDriveSync.exe --mode browser --headless --watch
```

---

## 📂 Project Structure

```text
gdrive-documents-sync/
├── gdrive_documents_sync.py   # Main CLI entry point & sync engines
├── requirements.txt           # Python package dependencies
├── credentials.json           # (Optional) OAuth 2.0 client secret for API mode
├── gdrive_browser_profile/    # (Auto-generated) Persistent Chromium session data
├── sync.log                   # (Auto-generated) Detailed execution & error logs
└── README.md                  # Project documentation
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for full details.
