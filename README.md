# Mixxx-Anywhere: Portable Library Sync
A robust solution for running a **Mixxx** DJ setup from a portable drive (USB/SSD) or a synced cloud folder (Dropbox/OneDrive) across both **Linux** and **Windows** without losing track analysis, cues, or playlists.

## 1. The Problem
Mixxx stores all track locations, metadata (BPM, Key), and configuration settings using **absolute paths** (e.g., `C:\Users\User\Music\...` or `/home/User/Music/...`).

When you move your library between a Linux machine and a Windows machine, or even between two Windows machines with different drive letters:
1. Mixxx marks all tracks as "Missing."
2. A rescan creates duplicates with no BPM or Cue data.
3. Hardware settings (Audio/MIDI) for Linux often crash or mess up Windows settings, and vice versa.

## 2. The Solution
This project uses a "Smart Launcher" system. Before Mixxx opens, a Python engine:
*   Detects the current path of the folder.
*   Swaps in the correct Hardware Configuration for the current OS.
*   Rewrites the SQLite Database paths to match the current machine.
*   Cleans up "Ghost" entries to prevent duplicates.
*   Uses a **Portable Python** environment so it works on any Windows PC, even without Python installed.

---

## 3. Folder Structure
```text
/Mixxx_Portable/
├── start_smart_lin.sh       # Linux Entry Point
├── start_smart_win.bat      # Windows Entry Point
├── Music/                   # Your actual .mp3/.flac files
└── Mixxx_Data/              # The --settingsPath folder
    ├── mixxxdb.sqlite       # The Library Database
    ├── mixxx.cfg            # The active config (overwritten on launch)
    ├── mixxx.cfg.lin        # Backup of Linux-specific hardware settings
    ├── mixxx.cfg.win        # Backup of Windows-specific hardware settings
    ├── mixxx_path_fixer.py  # The Logic Engine (Python)
    └── python_win/          # (Optional) Windows Embeddable Python folder
```

---

## 4. File Descriptions

### `start_smart_win.bat` / `start_smart_lin.sh`
These are the launchers. They perform four tasks:
1.  **Restore:** Copies `mixxx.cfg.win` (or `.lin`) to the active `mixxx.cfg`. This ensures your ASIO drivers stay on Windows and your ALSA/Jack settings stay on Linux.
2.  **Fix:** Runs the Python script to align database paths to the current drive letter/mount point.
3.  **Launch:** Opens Mixxx using the `--settingsPath` argument to keep data inside the portable folder.
4.  **Save:** When Mixxx closes, it copies the active config back to the backup (`.win` or `.lin`) to save any changes made during the session.

### `mixxx_path_fixer.py` (The Logic Engine)
This script is the core of the project. It performs "Brain Surgery" on the Mixxx SQLite database:
*   **Anchor Logic:** It looks for the folder name `Mixxx_Portable/Music` as an anchor. It discards everything before it (the "old" path) and attaches the "new" current path.
*   **Ghost Cleaning:** It finds tracks Mixxx marked as "deleted" (from the previous OS) and purges them before the path update to prevent "Unique Constraint" errors and duplicates.
*   **Recursive Safety:** It uses advanced string splitting (`split()[-1]`) to ensure that if a path is already partially correct, it doesn't accidentally double-up (e.g., `/Music/Music/track.mp3`).

### `python_win/`
A minimal, embeddable version of Python for Windows. This allows the script to run on any computer without requiring the user to install Python.

---

## 5. Development History: What We Solved

### Attempt 1: Simple String Replacement
*   **Result:** Failed. 
*   **Reason:** If the drive letter changed from `D:` to `E:`, the script didn't know the "old" prefix to replace.

### Attempt 2: SQLite Anchor Search
*   **Result:** Partially worked.
*   **Reason:** Created "Double Paths" (e.g., `C:/Music/Music/...`). If the script ran twice, it kept adding the folder name to itself.

### Attempt 3: Config Section Targeting
*   **Result:** Partially worked.
*   **Reason:** Mixxx would still rescan and lose BPM/Cues because "Ghost entries" existed in the database. SQLite would block the update of the "Good" data because the "Ghost" data already occupied that path slot.

### Attempt 4: The "Final Boss" Script (Current)
*   **Result:** **Success.**
*   **Logic:**
    1.  Delete all `mixxx_deleted = 1` tracks (the ghosts).
    2.  Use Python's path-handling to find the absolute end of the file path.
    3.  Explicitly reconstruct the path from scratch using the current detected root.
    4.  Force-inject the `Directory` key into the `[Library]` section of the config.

---

## 6. How to Use

### Setup
1.  **Mixxx:** Install Mixxx normally on your machines.
2.  **Clone Repo** Clone the Repository to your shared drive. On Linux: run `chmod +x start_smart_lin.sh´ to make the file executable
3.  **Initial Move:** Move your music into the `Music/` folder and your existing Mixxx settings (from `/AppData/Local/mixxx` or `~/.mixxx`) into `Mixxx_Data/`. Or Mixxx will generate new ones at the first start.

### Daily Use
*   **On Windows:** Double-click `start_smart_win.bat`.
*   **On Linux:** Run `bash start_smart_lin.sh`.

### Important Rules
*   **Do not enable "Rescan on Startup":** Let the script handle the paths. If Mixxx rescans before the script finishes, it might create temporary duplicates.
*   **Keep the Anchor:** Do not rename the `Mixxx_Portable` folder, as the script looks for this specific name to calculate paths.

---

## 7. Troubleshooting
*   **Duplicates appear:** Run the launcher, and inside Mixxx, go to `Library -> Clean up Library`. This usually happens if you manually moved files without using the script.
*   **Analysis Lost:** This happens if Mixxx rescans on an OS before the script runs. The current script prevents this by deleting the "New/Empty" tracks and restoring the "Old/Analyzed" tracks to the active path.

## 8. Add new Music
To ensure your new music is synced across both Windows and Linux, you must follow the **"Golden Rule"** of this setup: **All music files must stay inside the `Music/` folder on your portable drive.**

Here is the step-by-step workflow for adding new tracks:

### 1. Copy the Files
*   Plug in your drive/Open your Dropbox folder.
*   Copy your new MP3s, WAVs, or FLACs into the `Mixxx_Portable/Music/` folder.
*   You can create subfolders (e.g., `Music/2024/Techno/`) as much as you like, as long as they are inside that main `Music` anchor.

### 2. Launch Mixxx (Using the Smart Launcher)
*   Run `start_smart_win.bat` or `start_smart_lin.sh`.
*   The script will run first. It won't find the "new" files yet because they aren't in the database, but it will prepare the environment for them.

### 3. Trigger a Rescan in Mixxx
Once Mixxx is open:
*   Go to the **Library** sidebar.
*   Right-click on **Tracks** (or any folder).
*   Select **Rescan Library**.
*   Mixxx will find the new files. Because the script correctly set the "Library Directory" in your config, Mixxx will save the new tracks into the database using the correct path for the machine you are currently on.

### 4. Switch Systems
When you move to the other OS (e.g., from Windows to Linux):
1.  Run the **Smart Launcher** for that OS.
2.  The script will detect those brand-new entries you just added on the other system.
3.  It will strip the "Windows" part of the path and replace it with the "Linux" part.
4.  When Mixxx opens, your new music will be there, ready to play, with any cues or BPM analysis you performed on the first machine.

---

### ⚠️ Important: What NOT to do
*   **Don't add music from your desktop/downloads folder:** If you add a track located at `C:\Users\Bashi\Downloads\track.mp3`, the script will **not** fix it because it doesn't contain the `Mixxx_Portable` anchor. When you move to Linux, that file will be "Missing" forever.
*   **Don't use the "Add Music" button in Mixxx to point to external folders:** Always move the file onto the portable drive **first**, then scan it.
*   **Avoid "Rescan on Startup":** It is still better to trigger the scan manually once Mixxx is open. This ensures the Python script has finished its "surgery" on the existing database entries before Mixxx starts looking for new ones.

### Pro-Tip:

If you have a lot of new music, you can analyze it (BPM/Key/Beatgrid) on one machine (e.g., your powerful Windows PC), and thanks to the script, all that analysis data will be perfectly preserved when you open that same drive on your Linux laptop later!



