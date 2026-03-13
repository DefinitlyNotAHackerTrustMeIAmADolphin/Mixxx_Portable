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
    """Try to open a file multiple times to bypass cloud-sync locks."""
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

def get_old_root_from_db(db_path, root_name):
    """Interrogates the database to find exactly what base path it is currently using."""
    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cur = conn.cursor()
        # Look in the directories table first
        cur.execute("SELECT directory FROM directories WHERE directory LIKE ? LIMIT 1", (f"%{root_name}%",))
        row = cur.fetchone()
        
        # Fallback to track_locations if directories is empty
        if not row:
            cur.execute("SELECT location FROM track_locations WHERE location LIKE ? LIMIT 1", (f"%{root_name}%",))
            row = cur.fetchone()
            
        conn.close()
        
        if row and row[0]:
            path_str = row[0].replace("\\", "/")
            idx = path_str.rfind(root_name)
            if idx != -1:
                return path_str[:idx + len(root_name)]
    except Exception:
        pass
    return None

def validate_library(db_path, current_root):
    if not os.path.exists(db_path): return
    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cur = conn.cursor()
        cur.execute("SELECT location FROM track_locations WHERE location NOT LIKE ?", (f"{current_root}%",))
        external_tracks = cur.fetchall()
        if external_tracks:
            print("\n" + "!"*60)
            print("⚠️  WARNING: NON-PORTABLE TRACKS DETECTED")
            print(f"Found {len(external_tracks)} tracks outside your portable drive.")
            print("!"*60)
            for (path,) in external_tracks[:5]: print(f" -> {path[0]}")
            print("!"*60 + "\n")
        conn.close()
    except Exception: pass

def fix_paths(data_dir, to_os, mode="load"):
    data_dir = os.path.abspath(data_dir)
    portable_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_name = os.path.basename(portable_root) 
    
    db_path = os.path.join(data_dir, "mixxxdb.sqlite")
    cfg_active = os.path.join(data_dir, "mixxx.cfg")
    config_dir = os.path.join(data_dir, "Configs")
    backup_dir = os.path.join(data_dir, "Backups")
    
    # Clean up the flawed state file from the previous version if it exists
    db_state_file = os.path.join(data_dir, ".portable_root")
    if os.path.exists(db_state_file):
        try: os.remove(db_state_file)
        except: pass
    
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)

    hostname = socket.gethostname().lower()
    current_root = mixxx_normalize_path(portable_root)
    
    os_ext = to_os[:3].lower()
    machine_cfg_store = os.path.join(config_dir, f"mixxx.cfg.{hostname}")
    os_template_store = os.path.join(config_dir, f"mixxx.cfg.{os_ext}") 

    print(f"--- Mixxx Sync[{to_os.upper()} | Machine: {hostname}] ---")

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
    else:
        # THE SMART SCRUB: Wipe audio hardware on an unknown machine, keep everything else!
        print(f"No template found for {hostname} or {to_os}.")
        if os.path.exists(cfg_active):
            print("Sanitizing config: Wiping old audio hardware to prevent OS crashes...")
            try:
                with robust_open(cfg_active, 'r') as f:
                    cfg_lines = f.readlines()
                
                safe_lines =[]
                in_hardware_block = False
                for line in cfg_lines:
                    s = line.strip()
                    if s.startswith("[") and s.endswith("]"):
                        # If we hit the Soundcard block, flag it to skip writing those lines
                        in_hardware_block = (s == "[Soundcard]")
                            
                    if not in_hardware_block:
                        safe_lines.append(line)
                        
                with robust_open(cfg_active, 'w') as f:
                    f.writelines(safe_lines)
            except Exception as e:
                print(f"Config Sanitizer Error: {e}")

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
        old_root = get_old_root_from_db(db_path, root_name)
        
        if old_root and old_root != current_root:
            try:
                conn = sqlite3.connect(db_path, timeout=15.0)
                cur = conn.cursor()
                cur.execute("DELETE FROM track_locations WHERE id IN (SELECT location FROM library WHERE mixxx_deleted = 1)")
                cur.execute("DELETE FROM library WHERE mixxx_deleted = 1")
                
                targets =[
                    ("track_locations", "location", "id"), ("track_locations", "directory", "id"),
                    ("library", "location", "id"), ("library", "folder", "id"),
                    ("LibraryHashes", "directory_path", "directory_path"),
                    ("directories", "directory", "directory")
                ]

                for table, col, pkey in targets:
                    cur.execute(f"PRAGMA table_info({table})")
                    if any(col == c[1] for c in cur.fetchall()):
                        # Only target paths that exactly match the old database root
                        cur.execute(f"SELECT {pkey}, {col} FROM {table} WHERE {col} LIKE ?", (f"{old_root}%",))
                        rows = cur.fetchall()
                        
                        updates =[]
                        for pk, old_path in rows:
                            if not old_path: continue
                            clean_old = old_path.replace("\\", "/")
                            # Replace the old root with the current machine's root
                            new_path = clean_old.replace(old_root, current_root, 1)
                            
                            if clean_old != new_path:
                                updates.append((new_path, pk))
                        
                        if updates:
                            cur.executemany(f"UPDATE {table} SET {col} = ? WHERE {pkey} = ?", updates)
                            total_updated += len(updates)
                            
                conn.commit()
                conn.close()
                print(f"[SUCCESS] Database: Updated {total_updated} file path entries.")
            except Exception as e: print(f"Database Error: {e}")
        else:
            print("[INFO] Database paths already match the current system. No DB updates needed.")

    # Config File Reconstruction
    if os.path.exists(cfg_active):
        try:
            with robust_open(cfg_active, 'r') as f:
                lines = f.readlines()
            
            new_lines =[]
            cfg_fixes = 0
            for line in lines:
                clean_line = line.replace("\\", "/")
                
                if root_name in clean_line:
                    # Parse the exact path prefix stored in the config file dynamically
                    parts = clean_line.split(" ", 1)
                    if len(parts) == 2:
                        key, val = parts
                        v_idx = val.rfind(root_name)
                        if v_idx != -1:
                            old_cfg_root = val[:v_idx + len(root_name)]
                            if old_cfg_root != current_root:
                                new_val = val.replace(old_cfg_root, current_root, 1)
                                new_line = f"{key} {new_val}"
                                if line != new_line: cfg_fixes += 1
                                new_lines.append(new_line)
                                continue
                
                new_lines.append(line)
            
            if cfg_fixes > 0:
                with robust_open(cfg_active, 'w') as f:
                    f.writelines(new_lines)
                print(f"[SUCCESS] Config: Applied {cfg_fixes} path updates.")
            else:
                print("[INFO] Config paths already match the current system. No cfg updates needed.")
        except Exception as e: print(f"Config Error: {e}")

    validate_library(db_path, current_root)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        fix_paths(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "load")