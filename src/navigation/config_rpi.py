# ------------------------------------------------------------------------------
# Raspberry Pi 3B+ Optimized Configuration
# ------------------------------------------------------------------------------
# Optimized settings for RPi 3B+ with minimal processing power
# Use this config on RPi, switch back to config.py on desktop
# ------------------------------------------------------------------------------

# Camera settings - REDUCED for RPi performance
CAMERA_WIDTH = 320  # Reduced from 640 (4x fewer pixels to process)
CAMERA_HEIGHT = 240  # Reduced from 480
CAMERA_FPS = 15  # Reduced from 30 (RPi camera can't sustain high FPS with processing)

# YOLO model settings
YOLO_MODEL = "yolo11n.pt"  # Keep nano model
CONFIDENCE_THRESHOLD = 0.5  # Increased to reduce false positives
IOU_THRESHOLD = 0.5

# CRITICAL: Model inference settings for RPi
# These override YOLO's default settings for speed
YOLO_INFERENCE_SIZE = 320  # Use smaller input size (default is 640)
YOLO_DEVICE = "cpu"  # RPi doesn't have GPU
YOLO_HALF_PRECISION = False  # RPi ARM doesn't support FP16
YOLO_MAX_DETECTIONS = 10  # Limit number of detections processed

# Zone boundaries (as fraction of frame width)
ZONE_LEFT_END = 0.33
ZONE_RIGHT_START = 0.67

# Persistence settings - RELAXED for lower FPS
PERSISTENCE_FRAMES = 2  # Reduced from 3 (since we have fewer frames/sec)
MAX_TRACKING_DISTANCE = 80  # Reduced for smaller resolution

# Audio settings
TTS_ENABLED = True
TTS_RATE = 175
MESSAGE_COOLDOWN = 6.0  # Increased to reduce CPU usage on TTS
GLOBAL_COOLDOWN = 2.0  # Increased from 1.5s

# Performance settings
SKIP_FRAMES = 2  # Process every Nth frame (1=all, 2=every other, 3=every third)
DISPLAY_ENABLED = False  # Disable video window on RPi (saves CPU)
STATS_ENABLED = False  # Disable FPS stats overlay
VERBOSE_LOGGING = False  # Reduce console output

# Object priorities (same as config.py)
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
