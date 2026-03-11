import sqlite3
import os
import sys

def mixxx_normalize_path(path_str):
    """Mixxx requires forward slashes and uppercase drive letters on all OSes."""
    path_str = path_str.replace('\\', '/')
    if len(path_str) >= 2 and path_str[1] == ':':
        path_str = path_str[0].upper() + path_str[1:]
    return path_str

def fix_paths(data_dir, to_os):
    # 1. SETUP PATHS
    portable_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(data_dir, "mixxxdb.sqlite")
    cfg_path = os.path.join(data_dir, "mixxx.cfg")

    # Normalize our base directories immediately to Mixxx standards
    current_root = mixxx_normalize_path(portable_root)
    current_music_dir = current_root + "/Music"

    print(f"--- Mixxx Sync [{to_os.upper()}] ---")
    print(f"Target Music Path: {current_music_dir}")

    # --- PART A: DATABASE FIX ---
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            print("Cleaning up database ghost entries...")
            cur.execute("DELETE FROM track_locations WHERE id IN (SELECT location FROM library WHERE mixxx_deleted = 1)")
            cur.execute("DELETE FROM library WHERE mixxx_deleted = 1")
            cur.execute("DELETE FROM track_locations WHERE id NOT IN (SELECT location FROM library)")
            
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
                            
                            # CRITICAL FIX: String concatenation ensures we keep the forward slash!
                            new_path = f"{current_music_dir}/{sub_path}"
                            
                            try:
                                cur.execute(f"UPDATE {table} SET {col} = ? WHERE {pkey} = ?", (new_path, pk))
                            except sqlite3.IntegrityError:
                                cur.execute(f"DELETE FROM {table} WHERE {pkey} = ?", (pk,))

            conn.commit()
            print("Database: Path reconstruction complete.")
        except Exception as e:
            print(f"Database Error: {e}")
        finally:
            conn.close()

    # --- PART B: CONFIG FILE FIX ---
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            new_lines =[]
            in_library_section = False

            for line in lines:
                stripped = line.strip()
                
                if stripped == "[Library]":
                    in_library_section = True
                elif stripped.startswith("[") and stripped.endswith("]"):
                    in_library_section = False

                if (in_library_section or stripped.startswith("Directory")) and stripped.startswith("Directory"):
                    new_lines.append(f"Directory {current_music_dir}\n")
                elif stripped.startswith("RecordingDirectory"):
                    new_lines.append(f"RecordingDirectory {current_music_dir}\n")
                elif "Mixxx_Portable" in line:
                    key = line.split(" ")[0]
                    clean_line = line.replace("\\", "/")
                    if "Mixxx_Portable/" in clean_line:
                        sub_path = clean_line.split("Mixxx_Portable/")[-1].strip()
                        new_val = f"{current_root}/{sub_path}"
                        new_lines.append(f"{key} {new_val}\n")
                    else:
                        new_lines.append(line) # Leave standard lines alone
                else:
                    new_lines.append(line)

            with open(cfg_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print("Config: Path reconstruction complete.")
        except Exception as e:
            print(f"Config Error: {e}")

if __name__ == "__main__":
    fix_paths(sys.argv[1], sys.argv[2])
