import sqlite3
import os
import sys
import shutil
import datetime
import glob
import socket
import time
import subprocess

def mixxx_normalize_path(path_str):
    if not path_str: return ""
    path_str = path_str.replace('\\', '/')
    if len(path_str) >= 2 and path_str[1] == ':':
        path_str = path_str[0].upper() + path_str[1:]
    return path_str

def is_mixxx_running():
    """Check if the Mixxx binary is specifically running."""
    try:
        if sys.platform == "win32":
            # Using /NH (no header) and CSV format for cleaner parsing
            cmd = 'tasklist /FI "IMAGENAME eq mixxx.exe" /FO CSV /NH'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', 'ignore')
            return "mixxx.exe" in output.lower()
        else:
            # -x ensures we match the exact process name 'mixxx'
            result = subprocess.run(['pgrep', '-x', 'mixxx'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
    except: 
        return False

def check_environment(data_dir):
    print("🔍 Checking Environment...")
    issues = []
    
    music_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Music")
    if not os.path.exists(music_dir):
        issues.append(f"- 'Music' folder not found. Please create: {music_dir}")
    
    if not os.path.exists(data_dir):
        try: os.makedirs(data_dir)
        except: issues.append(f"- Cannot create Mixxx_Data folder at {data_dir}")

    if issues:
        print("\n" + "!"*60)
        print("❌ SETUP ISSUES FOUND:")
        for issue in issues: print(issue)
        print("!"*60)
        input("\nPress Enter to try and continue anyway...")
        return False
    
    print("✅ Environment Healthy.")
    return True

def check_db_integrity(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        res = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        return res[0] == "ok"
    except: return False

def robust_open(file_path, mode, encoding='utf-8', retries=5, delay=0.2):
    for i in range(retries):
        try:
            return open(file_path, mode, encoding=encoding, errors='ignore')
        except (OSError, IOError):
            time.sleep(delay)
    return open(file_path, mode, encoding=encoding, errors='ignore')

def get_old_root_from_db(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cur = conn.cursor()
        cur.execute("SELECT directory FROM directories")
        rows = cur.fetchall()
        conn.close()
        for (path_str,) in rows:
            p = path_str.replace('\\', '/')
            if p.endswith('/Music'): return p[:-6]
    except Exception: pass
    return None

def validate_library(db_path, current_root):
    if not os.path.exists(db_path): return
    try:
        conn = sqlite3.connect(db_path, timeout=15.0)
        cur = conn.cursor()
        cur.execute("SELECT location FROM track_locations WHERE location NOT LIKE ?", (f"{current_root}%",))
        external = cur.fetchall()
        if external:
            print("\n" + "!"*60)
            print(f"⚠️  EXTERNAL TRACKS: {len(external)} files are not on this drive!")
            print("!"*60)
            for (path,) in external[:3]: print(f" -> {path[0]}")
            print("..." if len(external) > 3 else "")
            print("!"*60 + "\n")
        conn.close()
    except Exception: pass

def fix_paths(data_dir, to_os, mode="load"):
    # 1. Block multiple instances
    if mode == "load" and is_mixxx_running():
        print("\n" + "!"*60)
        print("❌ ERROR: MIXXX IS ALREADY RUNNING!")
        print("To prevent database corruption, you cannot run two instances.")
        print("Please close Mixxx and try again.")
        print("!"*60)
        # Force a pause so the window doesn't flash shut
        input("\nPress Enter to exit...")
        sys.exit(1)

    if mode == "load":
        check_environment(data_dir)

    data_dir = os.path.abspath(data_dir)
    portable_root_abs = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    current_root = mixxx_normalize_path(portable_root_abs)
    current_music_dir = f"{current_root}/Music"
    
    db_path = os.path.join(data_dir, "mixxxdb.sqlite")
    cfg_active = os.path.join(data_dir, "mixxx.cfg")
    config_dir = os.path.join(data_dir, "Configs")
    backup_dir = os.path.join(data_dir, "Backups")
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "controllers"), exist_ok=True)

    hostname = socket.gethostname().lower()
    print(f"--- Mixxx Sync [{to_os.upper()} | {hostname}] ---")

    if mode == "save":
        if os.path.exists(cfg_active):
            shutil.copy2(cfg_active, os.path.join(config_dir, f"mixxx.cfg.{hostname}"))
            print(f"[SUCCESS] Hardware settings saved.")
        return

    # 2. Integrity Check
    if os.path.exists(db_path):
        if not check_db_integrity(db_path):
            print("\n❌ DATABASE CORRUPTION DETECTED")
            backups = sorted(glob.glob(os.path.join(backup_dir, f"mixxxdb_{hostname}_*.sqlite")))
            if backups:
                latest = backups[-1]
                choice = input(f"Restore latest backup ({os.path.basename(latest)})? (y/N): ").lower()
                if choice == 'y':
                    shutil.copy2(latest, db_path)
                    print("Backup restored.")
                else: 
                    print("Aborted.")
                    input("Press Enter to exit...")
                    sys.exit(1)
            else:
                print("No backups found. Cannot proceed safely.")
                input("Press Enter to exit...")
                sys.exit(1)

    # 3. Hardware restoration
    machine_cfg = os.path.join(config_dir, f"mixxx.cfg.{hostname}")
    os_template = os.path.join(config_dir, f"mixxx.cfg.{to_os[:3].lower()}")
    if os.path.exists(machine_cfg):
        shutil.copy2(machine_cfg, cfg_active)
    elif os.path.exists(os_template):
        shutil.copy2(os_template, cfg_active)

    # 4. Backup
    if os.path.exists(db_path):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(db_path, os.path.join(backup_dir, f"mixxxdb_{hostname}_{ts}.sqlite"))
        for old in sorted(glob.glob(os.path.join(backup_dir, f"mixxxdb_{hostname}_*.sqlite")))[:-10]:
            try: os.remove(old)
            except: pass

    # 5. DB Migration
    if os.path.exists(db_path):
        old_root = get_old_root_from_db(db_path)
        if old_root and old_root != current_root:
            print(f"Migrating paths: {old_root} -> {current_root}")
            try:
                conn = sqlite3.connect(db_path, timeout=15.0)
                cur = conn.cursor()
                targets = [("track_locations", "location"), ("track_locations", "directory"),
                           ("LibraryHashes", "directory_path"), ("directories", "directory")]
                for table, col in targets:
                    cur.execute(f"PRAGMA table_info({table})")
                    if any(col == c[1] for c in cur.fetchall()):
                        cur.execute(f"UPDATE {table} SET {col} = ? || SUBSTR({col}, LENGTH(?) + 1) WHERE {col} LIKE ? || '%'", 
                                   (current_root, old_root, old_root))
                conn.commit()
                conn.close()
                print("[SUCCESS] Database updated.")
            except Exception as e: print(f"Database Error: {e}")

    # 6. Config Migration
    if os.path.exists(cfg_active):
        try:
            with robust_open(cfg_active, 'r') as f: lines = f.readlines()
            old_cfg_root = None
            for l in lines:
                if l.startswith("Directory ") and "/Music" in l:
                    old_cfg_root = l.replace("\\", "/").split("Directory ")[1].split("/Music")[0].strip()
                    break
            if old_cfg_root and old_cfg_root != current_root:
                with robust_open(cfg_active, 'w') as f:
                    f.writelines([l.replace(old_cfg_root, current_root) for l in lines])
                print("[SUCCESS] Config updated.")
        except: pass

    validate_library(db_path, current_root)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        fix_paths(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "load")