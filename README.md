# 🎧 Mixxx-Anywhere: Portable & Machine-Aware Sync

A robust solution for running a **Mixxx** DJ setup from a portable drive (USB/SSD) or a synced cloud folder (Dropbox/OneDrive) across multiple computers and operating systems (**Windows & Linux**) without losing track analysis, cues, playlists, or audio hardware settings.

---

## 🛠 The Problem vs. The Solution

### The Problem
1.  **Paths:** Mixxx uses absolute paths (e.g., `C:\Users\Name\Music\...`). Move to another computer or Linux, and your library "breaks."
2.  **Hardware:** Every computer has different soundcards. A Windows ASIO config will crash a Linux machine, and a laptop’s latency settings won't match a studio desktop.
3.  **Human Error:** It is easy to accidentally add a track from a "Downloads" folder that isn't on the portable drive, leading to "Missing Track" errors later.

### The Solution
The **Smart Launcher** handles the "surgery" before Mixxx starts:
*   **Machine-Specific Hardware:** It detects the unique **Hostname** of the computer and loads/saves a dedicated hardware config for *that specific machine* in a dedicated folder.
*   **Path Reconstruction:** It rewrites the SQLite database in real-time to match the current drive letter or mount point.
*   **The "Pre-Flight" Validator:** It scans your library before launching and warns you if any tracks are located outside the portable folder.
*   **Rolling Backups:** It maintains a self-cleaning history of your database, tagged by machine name and timestamp.

---

## 📂 Folder Structure
```text
/Mixxx_Portable/
├── start_smart_win.bat   # Windows Entry Point
├── start_smart_lin.sh    # Linux Entry Point
├── Music/                # THE ANCHOR: Put all your audio files here
├── Mixxx_Data/           # Your settingsPath folder
│   ├── mixxxdb.sqlite    # The ACTIVE Library Database
│   ├── mixxx.cfg         # The ACTIVE config (overwritten on launch)
│   ├── Configs/          # Machine-specific hardware settings
│   │   ├── mixxx.cfg.win      # Windows Generic Template
│   │   ├── mixxx.cfg.lin      # Linux Generic Template
│   │   ├── mixxx.cfg.dj-laptop
│   │   └── mixxx.cfg.studio-pc
│   └── Backups/          # Rolling DB backups (tagged by machine name)
└── Scripts/              
    └── mixxx_path_fixer.py   # The logic engine
```

---

## 🚀 Setup Guide

1.  **Install Mixxx** normally on your host machines.
2.  **Move your Music:** Place all your tracks inside the `/Music` folder of this repo.
3.  **Launch:** Run the `.bat` or `.sh` file.
4.  **Hardware Setup:** On the first run on any new machine, configure your Sound Hardware (latency, soundcard) in Mixxx.
5.  **Save:** When you close Mixxx, the script automatically saves those settings to `Mixxx_Data/Configs/mixxx.cfg.[your-hostname]`. Next time you use that machine, your settings will be waiting for you.

---

## 🛡️ The "Pre-Flight" Validator
Before Mixxx opens, the script checks your database for "Illegal" paths. If you added a song from your computer's `Desktop` or `Downloads` instead of the portable `/Music` folder, the terminal will display a high-visibility warning:

`⚠️ WARNING: NON-PORTABLE TRACKS DETECTED`

This allows you to move those files into the `/Music` folder and re-scan before you head to a gig where those local folders won't exist.

---

## 🎵 The "Golden Rule"
To ensure sync works, you **must** follow this rule:
> **All music files must stay inside the `/Music` folder on your portable drive.**

---

## 🔄 Future Plans & Work in Progress

### 🛡️ Improvement Suggestions (Stability & Safety)

1.  **macOS Support:**
    *   **Goal:** Add `start_smart_mac.sh`.
    *   **Note:** Needs to account for macOS mounting external drives under `/Volumes/`.

2.  **Graceful Error Handling for "Locked" Databases:**
    *   **The Problem:** If Mixxx crashes, a `.sqlite-journal` file may exist, locking the DB.
    *   **The Fix:** Add logic to check for journal files and warn the user before attempting the path-swap.

3.  **Expanded Logging & Transparency:**
    *   **Goal:** Show a summary of how many track paths were updated in the current session (e.g., `[SUCCESS] Updated 1,240 track paths`).

---

### ✨ Feature Requests (New Functionality)

1.  **Custom Controller Mapping Sync:**
    *   **The Feature:** Create a system to sync custom `.xml` and `.js` MIDI mappings across machines so your controllers work instantly everywhere.

2.  **Relative Pathing for Playlists (M3U Export):**
    *   **The Feature:** An option to export Mixxx playlists to standard `.m3u` files with relative paths.
    *   **Why:** Allows playing your music in other apps (VLC/Mobile) directly from the USB drive.

3.  **Binary Download Helper:**
    *   **The Feature:** A `setup_binaries.py` script to fetch the latest Mixxx portable ZIP and extract it into a `/bin` folder for a "Zero-Install" experience.

4.  **Cloud-Sync Status Checker:**
    *   **The Feature:** If using Dropbox/OneDrive, check if the database is currently "Syncing" before launching to prevent "Conflicted Copy" data loss.

---

## 📜 License
This project is licensed under the **GPL-3.0**. 

> 🐬 *Trust me, I'm a dolphin. Your database is in safe fins.*