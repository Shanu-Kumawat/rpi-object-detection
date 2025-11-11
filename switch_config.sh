#!/bin/bash
# ------------------------------------------------------------------------------
# Switch Between Desktop and Raspberry Pi Configurations
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/src/navigation"

show_usage() {
    echo "Usage: $0 {desktop|rpi|status}"
    echo ""
    echo "Commands:"
    echo "  desktop  - Switch to desktop/high-performance config"
    echo "  rpi      - Switch to Raspberry Pi optimized config"
    echo "  status   - Show current configuration"
    echo ""
}

show_status() {
    if [ -f "$CONFIG_DIR/config.py" ]; then
        echo "Current configuration:"
        echo ""
        grep "CAMERA_WIDTH\|CAMERA_HEIGHT\|YOLO_INFERENCE_SIZE\|SKIP_FRAMES\|DISPLAY_ENABLED" "$CONFIG_DIR/config.py" | head -5
    else
        echo "No config.py found!"
    fi
}

switch_to_desktop() {
    if [ -f "$CONFIG_DIR/config_original.py" ]; then
        cp "$CONFIG_DIR/config_original.py" "$CONFIG_DIR/config.py"
        echo "✓ Switched to DESKTOP configuration"
        echo "  - Resolution: 640x480"
        echo "  - Inference: 640x640 (default)"
        echo "  - Frame skip: None"
        echo "  - Display: Enabled"
    else
        echo "✗ Desktop config not found! Using default..."
        # Create from rpi config as base
        if [ -f "$CONFIG_DIR/config_rpi.py" ]; then
            cat > "$CONFIG_DIR/config.py" << 'EOF'
# Desktop configuration
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

YOLO_MODEL = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.45
IOU_THRESHOLD = 0.5

ZONE_LEFT_END = 0.33
ZONE_RIGHT_START = 0.67

PERSISTENCE_FRAMES = 3
MAX_TRACKING_DISTANCE = 100

TTS_ENABLED = True
TTS_RATE = 175
MESSAGE_COOLDOWN = 5.0
GLOBAL_COOLDOWN = 1.5

# Desktop-specific: no restrictions
SKIP_FRAMES = 1
DISPLAY_ENABLED = True
STATS_ENABLED = True

CLASS_PRIORITIES = {
    "person": 10,
    "bicycle": 8,
    "car": 9,
    "motorcycle": 8,
    "bus": 9,
    "truck": 9,
    "dog": 7,
    "cat": 7,
    "chair": 3,
    "couch": 4,
    "bed": 5,
    "dining table": 4,
    "potted plant": 2,
    "bench": 4,
    "backpack": 3,
    "handbag": 3,
    "suitcase": 3,
    "bottle": 2,
    "cup": 2,
    "laptop": 5,
    "mouse": 1,
    "keyboard": 1,
    "cell phone": 3,
    "book": 2,
    "clock": 1,
    "vase": 2,
    "scissors": 2,
    "teddy bear": 2,
    "sports ball": 3,
}
EOF
            echo "✓ Created desktop config"
        fi
    fi
}

switch_to_rpi() {
    if [ -f "$CONFIG_DIR/config_rpi.py" ]; then
        # Backup current config if not already backed up
        if [ ! -f "$CONFIG_DIR/config_original.py" ] && [ -f "$CONFIG_DIR/config.py" ]; then
            cp "$CONFIG_DIR/config.py" "$CONFIG_DIR/config_original.py"
            echo "Backed up current config to config_original.py"
        fi
        
        cp "$CONFIG_DIR/config_rpi.py" "$CONFIG_DIR/config.py"
        echo "✓ Switched to RASPBERRY PI configuration"
        echo "  - Resolution: 320x240"
        echo "  - Inference: 320x320"
        echo "  - Frame skip: 2 (every other frame)"
        echo "  - Display: Disabled"
        echo ""
        echo "Expected performance: 3-5 FPS on RPi 3B+"
    else
        echo "✗ RPi config not found at $CONFIG_DIR/config_rpi.py"
        exit 1
    fi
}

case "$1" in
    desktop)
        switch_to_desktop
        ;;
    rpi)
        switch_to_rpi
        ;;
    status)
        show_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
