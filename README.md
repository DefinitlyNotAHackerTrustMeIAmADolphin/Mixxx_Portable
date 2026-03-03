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
*   **Restores** the correct config for your current OS (ASIO for Win / ALSA for Linux).
*   **Rewrites** the SQLite database paths in real-time to match the current machine.
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
│   └── mixxx.cfg.lin     # Linux-specific hardware backup
└── Scripts/              # logic and path-fixing scripts
```

---

## 🚀 Setup Guide

### 1. Initial Preparation
1.  **Install Mixxx** normally on both your Windows and Linux machines.
2.  **Clone this repo** to your portable drive or cloud folder.
3.  **Move your Music:** Place all your tracks inside the `/Music` folder of this repo.
4.  **Move your Settings:** Copy your existing Mixxx data (from `AppData/Local/mixxx` or `~/.mixxx`) into the `Mixxx_Data/` folder.

### 2. Making it Work
*   **On Linux:** Run `chmod +x start_smart_lin.sh` to allow the script to execute.
*   **On Windows:** Ensure you have Python installed (the script will look for `python`).

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
    *   Swap your OS-specific sound settings.
    *   Fix all file paths in the database.
4.  **Inside Mixxx:** If you added new music, right-click "Tracks" and select **Rescan Library**.
5.  **Close Mixxx:** The launcher will automatically save your session's settings back to the correct OS backup file (`.win` or `.lin`).

---

## ⚠️ Important Rules & Troubleshooting

*   **Avoid "Rescan on Startup":** In Mixxx preferences, keep "Rescan on Startup" **OFF**. Let the Python script finish its "surgery" before Mixxx starts looking for files.
*   **Duplicate Tracks:** If duplicates appear, go to `Library -> Clean up Library`. This usually means you added music from a folder outside the `Music/` anchor.
*   **Analysis Lost:** This happens if you open Mixxx directly without using the "Smart Launcher." **Always use the `.bat` or `.sh` files.**

---

## 📜 License
This project is licensed under the **GPL-3.0**. 

> 🐬 *Trust me, I'm a dolphin. Your database is in safe fins.*
