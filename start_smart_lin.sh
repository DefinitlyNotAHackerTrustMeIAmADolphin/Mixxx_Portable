#!/bin/bash
# Get the folder where THIS script is
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="$DIR/Mixxx_Data"
SCRIPT_DIR="$DIR/Scripts"

echo "[LINUX MODE] Swapping in Linux settings..."

# Restore Linux hardware settings
if [ -f "$DATA_DIR/mixxx.cfg.lin" ]; then
    cp "$DATA_DIR/mixxx.cfg.lin" "$DATA_DIR/mixxx.cfg"
fi

# Run the fixer
python3 "$SCRIPT_DIR/mixxx_path_fixer.py" "$DATA_DIR" "linux"

# Launch Mixxx
mixxx --settingsPath "$DATA_DIR"

# Save Linux hardware settings
cp "$DATA_DIR/mixxx.cfg" "$DATA_DIR/mixxx.cfg.lin"