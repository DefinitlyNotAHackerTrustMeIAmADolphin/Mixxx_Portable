import sqlite3
import os
import sys
import shutil
import datetime
import glob
import socket
import time

def mixxx_normalize_path(path_str):
    path_str = path_str.replace('\\', '/')
    if len(path_str) >= 2 and path_str[1] == ':':
        path_str = path_str[0].upper() + path_str[1:]
    return path_str

def robust_open(file_path, mode, encoding='utf-8', retries=5, delay=0.2):
    """Try to open a file multiple times to bypass cloud-sync (Dropbox) locks."""
    for i in range(retries):
        try:
            return open(file_path, mode, encoding=encoding, errors='ignore')
        except (OSError, IOError) as e:
            if i == retries - 1:
                raise e
            time.sleep(delay)
    return open(file_path, mode, encoding=encoding)

def check_db_lock(db_path):
    journal = db_path + "-journal"
    wal = db_path + "-wal"
    if os.path.exists(journal) or os.path.exists(wal):
        print("\n" + "!"*60)
        print("⚠️  DATABASE IS LOCKED OR RECOVERING")
        print("Mixxx might still be running, or it didn't close properly.")
        print("!"*60)
        choice = input("Proceed anyway? (y/N): ").lower()
        if choice != 'y':
            sys.exit(1)

def validate_library(db_path):
    if not os.path.exists(db_path): return
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT location FROM track_locations WHERE location NOT LIKE '%Mixxx_Portable%'")
        external_tracks = cur.fetchall()
        if external_tracks:
            print("\n" + "!"*60)
            print("⚠️  WARNING: NON-PORTABLE TRACKS DETECTED")
            print(f"Found {len(external_tracks)} tracks outside your portable drive.")
            print("!"*60)
            for (path,) in external_tracks[:5]: print(f" -> {path}")
            print("!"*60 + "\n")
        conn.close()
    except Exception: pass

def fix_paths(data_dir, to_os, mode="load"):
    # Normalize path strings to prevent Windows 'Invalid Argument' errors
    data_dir = os.path.abspath(data_dir)
    portable_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(data_dir, "mixxxdb.sqlite")
    cfg_active = os.path.join(data_dir, "mixxx.cfg")
    config_dir = os.path.join(data_dir, "Configs")
    backup_dir = os.path.join(data_dir, "Backups")
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)

    hostname = socket.gethostname().lower()
    current_root = mixxx_normalize_path(portable_root)
    current_music_dir = current_root + "/Music"
    
    os_ext = to_os[:3].lower()
    machine_cfg_store = os.path.join(config_dir, f"mixxx.cfg.{hostname}")
    os_template_store = os.path.join(config_dir, f"mixxx.cfg.{os_ext}") 

    print(f"--- Mixxx Sync [{to_os.upper()} | Machine: {hostname}] ---")

    if mode == "save":
        if os.path.exists(cfg_active):
            shutil.copy2(cfg_active, machine_cfg_store)
            print(f"Hardware settings saved to: Configs/mixxx.cfg.{hostname}")
        return

    # --- LOAD MODE ---
    if os.path.exists(db_path):
        check_db_lock(db_path)

    if os.path.exists(machine_cfg_store):
        print(f"Found specific config for {hostname}. Restoring...")
        shutil.copy2(machine_cfg_store, cfg_active)
    elif os.path.exists(os_template_store):
        print(f"No machine-specific config. Using {to_os} template...")
        shutil.copy2(os_template_store, cfg_active)

    # Database Backup
    try:
        MAX_BACKUPS = 10 
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(db_path):
            db_backup = os.path.join(backup_dir, f"mixxxdb_{hostname}_{timestamp}.sqlite")
            shutil.copy2(db_path, db_backup)
        db_backups = sorted(glob.glob(os.path.join(backup_dir, f"mixxxdb_{hostname}_*.sqlite")))
        if len(db_backups) > MAX_BACKUPS:
            for old_db in db_backups[:-MAX_BACKUPS]: os.remove(old_db)
    except Exception as e: print(f"Backup Error: {e}")

    # Path Reconstruction
    total_updated = 0
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("DELETE FROM track_locations WHERE id IN (SELECT location FROM library WHERE mixxx_deleted = 1)")
            cur.execute("DELETE FROM library WHERE mixxx_deleted = 1")
            
            targets =[
                ("track_locations", "location", "id"), ("track_locations", "directory", "id"),
                ("library", "location", "id"), ("library", "folder", "id"),
                ("LibraryHashes", "directory_path", "directory_path")
            ]

            for table, col, pkey in targets:
                cur.execute(f"PRAGMA table_info({table})")
                if any(col == c[1] for c in cur.fetchall()):
                    cur.execute(f"SELECT {pkey}, {col} FROM {table} WHERE {col} LIKE '%Mixxx_Portable%'")
                    rows = cur.fetchall()
                    for pk, old_path in rows:
                        if not old_path: continue
                        clean_old = old_path.replace("\\", "/")
                        if "Mixxx_Portable/Music" in clean_old:
                            sub_path = clean_old.split("Mixxx_Portable/Music")[-1].lstrip("/")
                            new_path = f"{current_music_dir}/{sub_path}"
                            if clean_old != new_path:
                                cur.execute(f"UPDATE {table} SET {col} = ? WHERE {pkey} = ?", (new_path, pk))
                                total_updated += 1
            conn.commit()
            conn.close()
            print(f"[SUCCESS] Database: Updated {total_updated} file path entries.")
        except Exception as e: print(f"Database Error: {e}")

    # Config File Reconstruction (Using Robust Open)
    if os.path.exists(cfg_active):
        try:
            with robust_open(cfg_active, 'r') as f:
                lines = f.readlines()
            
            new_lines = []; cfg_fixes = 0
            in_lib = False
            for line in lines:
                s = line.strip()
                if s == "[Library]": in_lib = True
                elif s.startswith("[") and s.endswith("]"): in_lib = False

                if (in_lib or s.startswith("Directory")) and s.startswith("Directory"):
                    new_val = f"Directory {current_music_dir}\n"
                    if line != new_val: cfg_fixes += 1
                    new_lines.append(new_val)
                elif s.startswith("RecordingDirectory"):
                    new_val = f"RecordingDirectory {current_music_dir}\n"
                    if line != new_val: cfg_fixes += 1
                    new_lines.append(new_val)
                elif "Mixxx_Portable" in line:
                    key = line.split(" ")[0]
                    clean_line = line.replace("\\", "/")
                    if "Mixxx_Portable/" in clean_line:
                        sub_path = clean_line.split("Mixxx_Portable/")[-1].strip()
                        new_val = f"{key} {current_root}/{sub_path}\n"
                        if line != new_val: cfg_fixes += 1
                        new_lines.append(new_val)
                    else: new_lines.append(line)
                else: new_lines.append(line)
            
            with robust_open(cfg_active, 'w') as f:
                f.writelines(new_lines)
            print(f"[SUCCESS] Config: Applied {cfg_fixes} path updates.")
        except Exception as e: print(f"Config Error: {e}")

    validate_library(db_path)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        fix_paths(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "load")