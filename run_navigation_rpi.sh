#!/bin/bash
# ------------------------------------------------------------------------------
# Run Navigation System on Raspberry Pi with Optimized Settings
# ------------------------------------------------------------------------------

echo "Starting Navigation System (Raspberry Pi Optimized)..."

# Activate UV virtual environment
source .venv/bin/activate

# Backup original config
if [ ! -f "src/navigation/config_original.py" ]; then
    cp src/navigation/config.py src/navigation/config_original.py
    echo "Backed up original config to config_original.py"
fi

# Use RPi-optimized config
cp src/navigation/config_rpi.py src/navigation/config.py
echo "Using Raspberry Pi optimized configuration:"
echo "  - Resolution: 320x240"
echo "  - Inference size: 320"
echo "  - Frame skip: 2 (process every other frame)"
echo "  - Display: Disabled"
echo ""

# Run without display (headless mode)
python -m src.navigation.navigation_system --no-video

# Restore original config when done
if [ -f "src/navigation/config_original.py" ]; then
    cp src/navigation/config_original.py src/navigation/config.py
    echo "Restored original config"
fi
