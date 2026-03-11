import sqlite3
import os
import sys
import shutil
import datetime
import glob
import socket

def mixxx_normalize_path(path_str):
    """Mixxx requires forward slashes and uppercase drive letters on all OSes."""
    path_str = path_str.replace('\\', '/')
    if len(path_str) >= 2 and path_str[1] == ':':
        path_str = path_str[0].upper() + path_str[1:]
    return path_str

def validate_library(db_path):
    """Checks for tracks located OUTSIDE the portable folder."""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # We look for any track location that doesn't belong to our portable anchor
        cur.execute("SELECT location FROM track_locations WHERE location NOT LIKE '%Mixxx_Portable%'")
        external_tracks = cur.fetchall()

        if external_tracks:
            print("\n" + "!"*60)
            print("⚠️  WARNING: NON-PORTABLE TRACKS DETECTED")
            print(f"Found {len(external_tracks)} tracks located outside your portable drive.")
            print("These tracks will be MISSING when you switch computers!")
            print("!"*60)
            print("Examples of tracks to move into /Music:")
            for (path,) in external_tracks[:10]: # Show first 10
                print(f" -> {path}")
            if len(external_tracks) > 10:
                print(f" ... and {len(external_tracks) - 10} more.")
            print("!"*60 + "\n")
            # We don't exit/stop, just warn the user before Mixxx starts.
    except Exception as e:
        print(f"Validator Error: {e}")
    finally:
        conn.close()

def fix_paths(data_dir, to_os, mode="load"):
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
    
    machine_cfg_store = os.path.join(config_dir, f"mixxx.cfg.{hostname}")
    os_template_store = os.path.join(config_dir, f"mixxx.cfg.{to_os[:3].lower()}") 

    print(f"--- Mixxx Sync [{to_os.upper()} | Machine: {hostname}] ---")

    if mode == "save":
        if os.path.exists(cfg_active):
            shutil.copy2(cfg_active, machine_cfg_store)
            print(f"Hardware settings saved to: Configs/mixxx.cfg.{hostname}")
        return

    # --- LOAD MODE ---
    
    # 1. Hardware Config Swap
    if os.path.exists(machine_cfg_store):
        print(f"Found specific config for {hostname}. Restoring...")
        shutil.copy2(machine_cfg_store, cfg_active)
    elif os.path.exists(os_template_store):
        print(f"No machine-specific config. Using {to_os} template...")
        shutil.copy2(os_template_store, cfg_active)

    # 2. Database Backup
    try:
        MAX_BACKUPS = 10 
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(db_path):
            db_backup = os.path.join(backup_dir, f"mixxxdb_{hostname}_{timestamp}.sqlite")
            shutil.copy2(db_path, db_backup)
        
        db_backups = sorted(glob.glob(os.path.join(backup_dir, f"mixxxdb_{hostname}_*.sqlite")))
        if len(db_backups) > MAX_BACKUPS:
            for old_db in db_backups[:-MAX_BACKUPS]:
                os.remove(old_db)
    except Exception as e:
        print(f"Backup Error: {e}")

    # 3. Path Reconstruction
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM track_locations WHERE id IN (SELECT location FROM library WHERE mixxx_deleted = 1)")
            cur.execute("DELETE FROM library WHERE mixxx_deleted = 1")
            
            targets =[
                ("track_locations", "location", "id"),
                ("track_locations", "directory", "id"),
                ("library", "location", "id"),
                ("library", "folder", "id"),
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
                            try:
                                cur.execute(f"UPDATE {table} SET {col} = ? WHERE {pkey} = ?", (new_path, pk))
                            except sqlite3.IntegrityError:
                                cur.execute(f"DELETE FROM {table} WHERE {pkey} = ?", (pk,))
            conn.commit()
            print("Database: Path reconstruction complete.")
        finally:
            conn.close()

    # 4. Config File Reconstruction
    if os.path.exists(cfg_active):
        try:
            with open(cfg_active, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            new_lines =[]
            in_lib = False
            for line in lines:
                s = line.strip()
                if s == "[Library]": in_lib = True
                elif s.startswith("[") and s.endswith("]"): in_lib = False

                if (in_lib or s.startswith("Directory")) and s.startswith("Directory"):
                    new_lines.append(f"Directory {current_music_dir}\n")
                elif s.startswith("RecordingDirectory"):
                    new_lines.append(f"RecordingDirectory {current_music_dir}\n")
                elif "Mixxx_Portable" in line:
                    key = line.split(" ")[0]
                    clean_line = line.replace("\\", "/")
                    if "Mixxx_Portable/" in clean_line:
                        sub_path = clean_line.split("Mixxx_Portable/")[-1].strip()
                        new_lines.append(f"{key} {current_root}/{sub_path}\n")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            with open(cfg_active, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print("Config: Path reconstruction complete.")
        except Exception as e:
            print(f"Config Error: {e}")

    # 5. NEW: VALIDATE LIBRARY (The Safety Net)
    validate_library(db_path)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        d_dir = sys.argv[1]
        o_type = sys.argv[2]
        mode_flag = sys.argv[3] if len(sys.argv) > 3 else "load"
        fix_paths(d_dir, o_type, mode_flag)
    else:
        print("Usage: python helper.py <data_dir> <os_type> <load/save>")