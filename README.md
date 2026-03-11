***

# 🎧 Mixxx-Anywhere: Portable Library Sync
A robust solution for running a **Mixxx** DJ setup from a portable drive (USB/SSD) or a synced cloud folder (Dropbox/OneDrive) across both **Linux** and **Windows** without losing track analysis, cues, or playlists.

---

## 🛠 The Problem vs. The Solution

### The Problem
Mixxx stores all track locations and metadata (BPM, Cues) using **absolute paths** (e.g., `C:\Users\Name\Music\...`). 
When you move between Windows and Linux, or change drive letters:
1. Mixxx marks tracks as "Missing."
2. Rescanning creates duplicates and loses your analysis data.
3. Audio hardware settings for Linux often crash on Windows, and vice versa.

### The Solution
This project uses a **"Smart Launcher"** system. Before Mixxx opens, a Python logic engine:
*   **Detects** the current drive letter or mount point.
*   **Backs up** your library safely before any modifications, keeping a self-cleaning, rolling history of your last 5 sessions per OS.
*   **Restores** the correct config for your current OS (ASIO for Win / ALSA for Linux).
*   **Rewrites** the SQLite database paths in real-time to match the current machine using strict, Mixxx-compliant formatting.
*   **Cleans** "Ghost" entries to prevent duplicates.

---

## 📂 Folder Structure
```text
/Mixxx_Portable/
├── start_smart_win.bat   # Windows Entry Point
├── start_smart_lin.sh    # Linux Entry Point
├── Music/                # THE ANCHOR: Put all your audio files here
├── Mixxx_Data/           # Your settingsPath folder
│   ├── mixxxdb.sqlite    # The Library Database
│   ├── mixxx.cfg         # Active config
│   ├── mixxx.cfg.win     # Windows-specific hardware backup
│   ├── mixxx.cfg.lin     # Linux-specific hardware backup
│   └── Backups/          # Auto-generated rolling backups (e.g., mixxxdb_windows_20260311_181500.sqlite)
└── Scripts/              # logic and path-fixing scripts
```

---

## 🚀 Setup Guide

### 1. Initial Preparation
1.  **Install Mixxx** normally on both your Windows and Linux machines.
2.  **Clone this repo** to your portable drive or cloud folder.
3.  **Move your Music:** Place all your tracks inside the `/Music` folder of this repo.
4.  **Move your Settings:(optional)** Copy your existing Mixxx data (from `AppData/Local/mixxx` or `~/.mixxx`) into the `Mixxx_Data/` folder.
5.  **Initial start:** On the first run of the launcher, select the `Music` folder as your library directory.

### 2. Making it Work
*   **On Linux:** Run `chmod +x start_smart_lin.sh` to allow the script to execute.
*   **On Windows:** Ensure you have Python installed (the script will look for `python`). *Note: If using an embedded Python setup, ensure `sqlite3.dll` and `_sqlite3.pyd` are included!*

---

## 🎵 The "Golden Rule" for Music
To ensure sync works, you **must** follow this rule:
> **All music files must stay inside the `/Music` folder on your portable drive.**

If you add a track from your computer's "Downloads" or "Desktop" folder, the script cannot "fix" it. When you switch to another computer, that track will be missing. Always move files into the portable `/Music` folder **before** scanning them in Mixxx.

---

## 🔄 Daily Workflow

1.  **Plug in** your drive.
2.  **Launch** via `start_smart_win.bat` or `start_smart_lin.sh`.
3.  **The Script** will automatically:
    *   Create a timestamped, OS-tagged backup (deleting old ones so your drive doesn't overflow).
    *   Swap your OS-specific sound settings.
    *   Fix all file paths in the database.
4.  **Inside Mixxx:** If you added new music, right-click "Tracks" and select **Rescan Library**.
5.  **Close Mixxx:** The launcher will automatically save your session's settings back to the correct OS backup file (`.win` or `.lin`).

---

## ⚠️ Important Rules & Troubleshooting

*   **Avoid "Rescan on Startup":** In Mixxx preferences, keep "Rescan on Startup" **OFF**. Let the Python script finish its "surgery" before Mixxx starts looking for files.
*   **Duplicate Tracks:** If duplicates appear, go to `Library -> Clean up Library`. This usually means you added music from a folder outside the `Music/` anchor.
*   **Analysis Lost:** This happens if you open Mixxx directly without using the "Smart Launcher." **Always use the `.bat` or `.sh` files.**
*   **Startup issues:** On Linux, it can be a problem if you install Mixxx via the Software Manager or Flatpak. Try installing it via the package manager by running `sudo apt install mixxx` or equivalent on your machine.

---
## Future Plans & Work in Progress

### 🛡️ Improvement Suggestions (Stability & Safety)

1.  **macOS Support (The Missing Link):**
    *   **The Suggestion:** You have Windows and Linux covered (and our new backup system is already future-proofed to tag `mac` files!). Adding a `start_smart_mac.sh` would make this truly universal. 
    *   **Technical Tip:** macOS usually mounts external drives under `/Volumes/DRIVE_NAME/`. Your path-rewriting logic needs to account for this specific prefix.

2.  **Graceful Error Handling for "Locked" Databases:**
    *   **The Problem:** If Mixxx didn't close properly, the `.sqlite-journal` file might exist, and your script might fail to open the DB.
    *   **The Fix:** Add logic to check for journal files and warn the user (or wait for them to clear) before attempting the path-swap.

3.  **Expanded Logging & Transparency:**
    *   **The Suggestion:** The script currently prints path reconstruction success and backup timestamps. Expanding this to show exactly how many tracks were updated would be a great UX boost.
    *   *Example Output:* `[SUCCESS] Updated 1,240 track paths | Swapped to Windows ASIO config.`

---

### ✨ Feature Requests (New Functionality)

1.  **"Pre-Flight" Path Validator:**
    *   **The Feature:** A script that scans the database and warns the user if any tracks are located **outside** the `/Music` anchor folder.
    *   **Why:** This prevents users from accidentally adding a song from their "Downloads" folder, which will break the next time they use a different computer.

2.  **Relative Pathing for Playlists (M3U Export):**
    *   **The Feature:** An option to export all Mixxx playlists to standard `.m3u` files with relative paths within the portable folder.
    *   **Why:** This allows the user to play their music in other apps (like VLC or a phone) directly from the same USB drive.

3.  **Binary Download Helper:**
    *   **The Feature:** A `setup_binaries.py` script.
    *   **Why:** Since you can't distribute the Mixxx `.exe` easily via GitHub due to size/licensing, a script that fetches the latest stable ZIP from Mixxx.org and extracts it into a `/bin` folder would make the "Zero-Install" experience much smoother.

4.  **"Dry Run" Mode:**
    *   **The Feature:** A flag (e.g., `start_smart_win.bat --debug`) that shows what paths *would* be rewritten without actually changing the database.
    *   **Why:** Extremely helpful for users trying to debug why their library isn't syncing correctly on a new Linux distro.

5.  **Cloud-Sync Status Checker:**
    *   **The Feature:** If the user is using Dropbox/OneDrive, the script checks if `mixxxdb.sqlite` is currently "Syncing" (locked by the cloud client) before launching.
    *   **Why:** Prevents "Conflicted Copy" files which can result in lost DJ sets/history.

---

## 📜 License
This project is licensed under the **GPL-3.0**. 

> 🐬 *Trust me, I'm a dolphin. Your database is in safe fins.*
