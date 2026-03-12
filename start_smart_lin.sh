#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="$DIR/Mixxx_Data"
SCRIPT_DIR="$DIR/Scripts"

# 1. Prepare Environment (LOAD mode)
python3 "$SCRIPT_DIR/mixxx_path_fixer.py" "$DATA_DIR" "linux" "load"

# 2. Launch Mixxx
mixxx --settingsPath "$DATA_DIR"

# 3. Post-Flight (SAVE mode)
echo "Mixxx closed. Saving machine-specific hardware settings..."
python3 "$SCRIPT_DIR/mixxx_path_fixer.py" "$DATA_DIR" "linux" "save"