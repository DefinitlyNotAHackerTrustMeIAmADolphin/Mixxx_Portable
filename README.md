This is a great addition. On Linux and macOS, scripts are often blocked from running until the user explicitly grants "Execute" permissions. Adding these commands to the README will save users a lot of frustration.

***

# 🎧 Mixxx-Anywhere: Professional Portable & Cloud Sync

**Mixxx-Anywhere** is a robust, logic-driven wrapper for the [Mixxx DJ software](https://mixxx.org). It allows you to run a fully synced DJ setup from a portable drive (USB/SSD) or a cloud-synced folder (Dropbox/OneDrive) across **Windows, Linux, and macOS** without ever seeing a "Missing Track" error or a database crash.

## 🌟 Why use this?

Mixxx traditionally stores paths as "Absolute Paths" (e.g., `C:\Users\DJ\Music\...`). If you move your drive to a different computer where the drive letter changes, or switch to Linux where paths look like `/media/dj/...`, your entire library breaks.

**Mixxx-Anywhere solves this by:**
1.  **Dynamic Path Reconstruction:** Identifies your current location and rewrites the SQLite database and `mixxx.cfg` in real-time.
2.  **Hardware Awareness:** Saves unique audio hardware settings (latency, soundcard IDs) for every computer you use.
3.  **Cloud-Sync Safety:** Prevents data loss caused by "Conflicted Copies" when Dropbox/OneDrive hasn't finished syncing between machines.

---

## 🚀 Key Features

*   **Structure-Based Detection:** Rename your portable folder to anything you like. The script dynamically deduces the root by locating your `/Music` anchor.
*   **Cloud-Sync "Dirty Flag":** Detects if the database was last used on a different machine. If the other machine hasn't finished uploading to the cloud, the script warns you before you create a sync conflict.
*   **Performance Optimization:** Automatically triggers `VACUUM` and `PRAGMA optimize` on exit to keep library searches lightning-fast.
*   **Smart Hardware Scrub:** On brand-new computers, the script "scrubs" only the audio hardware section of the config to prevent OS crashes.
*   **Process Guard:** Prevents launching a second instance of Mixxx, the leading cause of portable database corruption.
*   **Session Logging:** Maintains a `launcher_log.txt` for easy debugging of path migrations.

---

## 📂 Folder Structure

```text
/Your_Portable_Drive/
├── start_smart_win.bat   # Windows Entry Point
├── start_smart_lin.sh    # Linux Entry Point
├── start_smart_mac.sh    # macOS Entry Point
├── Music/                # THE ANCHOR: Put ALL your audio files here
├── Mixxx_Data/           # Your portable settingsPath folder
│   ├── mixxxdb.sqlite    # The ACTIVE Library Database
│   ├── mixxx.cfg         # The ACTIVE config (swapped per session)
│   ├── launcher_log.txt  # History of path migrations
│   ├── .mixxx_is_active  # Hidden sync-protection flag
│   ├── controllers/      # Your custom MIDI mappings
│   ├── Configs/          # Machine-specific hardware backups
│   └── Backups/          # Rolling DB backups (10 per machine)
└── Scripts/              
    ├── mixxx_path_fixer.py   # The Logic Engine
    └── python_win/           # (Optional) Portable Python for Windows
```

---

## 🛠 Prerequisites

### **Windows**
*   Install Mixxx in the default location (`C:\Program Files\Mixxx`).
*   Ensure the `python_win` folder exists in `Scripts/` or install Python 3.

### **Linux (Ubuntu/Debian/Pop!_OS)**
*   **Install Python 3:** `sudo apt install python3`
*   **Install Mixxx:** `sudo add-apt-repository ppa:mixxx/mixxx && sudo apt update && sudo apt install mixxx`
*   **Permissions:** Open a terminal in your portable folder and run:
    `chmod +x start_smart_lin.sh`

### **macOS**
*   **Install Mixxx:** Download from [mixxx.org](https://mixxx.org/download/).
*   **Permissions:** Open a terminal in your portable folder and run:
    `chmod +x start_smart_mac.sh`
*   **System Privacy:** Go to *System Settings > Privacy & Security > Files and Folders* and ensure **Mixxx** has permission to access **Removable Volumes**.

---

## 🏃‍♂️ Quick Start

1.  **Copy this project** to your USB drive or Dropbox folder.
2.  **Move your tracks** into the `/Music` folder.
3.  **Launch** using the `start_smart` file for your current OS.
4.  **First Run:** Set your **Sound Hardware**. When you close Mixxx, the script saves these settings for *this specific computer*.

---

## ⚠️ The "Golden Rule"

To keep your library 100% synced, you **must** follow this rule:
> **All music files must stay inside the `/Music` folder on your portable drive.**

---

## 🔍 Troubleshooting

| Message | Meaning | Fix |
| :--- | :--- | :--- |
| `❌ ERROR: MIXXX IS ALREADY RUNNING` | A Mixxx process is already active. | Close all Mixxx windows. |
| `⚠️ CLOUD-SYNC WARNING` | Database was last used on [Machine X]. | Ensure [Machine X] has finished uploading to the cloud before clicking 'y'. |
| `❌ DATABASE CORRUPTION DETECTED` | The file is unreadable. | Choose 'y' to restore the latest backup. |
| `ℹ️ NO DATABASE FOUND` | You deleted the DB or this is a fresh install. | Mixxx will create a new one on launch. |

---

## 📂 Manual Database Restoration

1.  **Close Mixxx** and the Smart Launcher.
2.  **Navigate to `/Mixxx_Data/Backups/`** and find the most recent healthy `.sqlite` file for your machine.
3.  **Copy it** into `/Mixxx_Data/`.
4.  **Delete the broken `mixxxdb.sqlite`** and rename your copy to `mixxxdb.sqlite`.
5.  **Launch** the script; it will automatically update the paths in the restored file.

---

## 🛠 Future Plans & WIP

*   **M3U Playlist Export:** Automatically generate portable relative-path playlists for use in VLC or mobile apps.
*   **Music Fetcher:** A script to find tracks scattered across your host computer and "collect" them into the `/Music` folder.
*   **Binary Download Helper:** A "Zero-Install" script to download portable Mixxx binaries directly to the drive.
*   **GUI Wrapper:** A simple visual interface to replace the terminal window.
*   **Automatic Offsite Backups:** Integration with Backblaze/S3 for secondary library protection.

---

## 📜 License
This project is licensed under the **GPL-3.0**. 

> 🐬 *Trust me, I'm a dolphin. Your database is in safe fins.*