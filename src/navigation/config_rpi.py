# ------------------------------------------------------------------------------
# Raspberry Pi 3B+ Optimized Configuration
# ------------------------------------------------------------------------------
# Optimized settings for RPi 3B+ with minimal processing power
# Use this config on RPi, switch back to config.py on desktop
# ------------------------------------------------------------------------------

# Camera settings - REDUCED for RPi performance
CAMERA_WIDTH = 160  # Reduced from 640 (4x fewer pixels to process)
CAMERA_HEIGHT = 120  # Reduced from 480
CAMERA_FPS = 10  # Reduced from 15 for better processing time

# YOLO model settings
YOLO_MODEL = "yolo11n.pt"  # Keep nano model
CONFIDENCE_THRESHOLD = 0.6  # Increased to reduce false positives and processing
IOU_THRESHOLD = 0.5

# CRITICAL: Model inference settings for RPi
# These override YOLO's default settings for speed
YOLO_INFERENCE_SIZE = 192  # Reduced from 256 (smaller = faster)
YOLO_DEVICE = "cpu"  # RPi doesn't have GPU
YOLO_HALF_PRECISION = False  # RPi ARM doesn't support FP16
YOLO_MAX_DETECTIONS = 5  # Reduced from 10 (fewer objects to process)

# Zone boundaries (as fraction of frame width)
ZONE_LEFT_END = 0.33
ZONE_RIGHT_START = 0.67

# Persistence settings - RELAXED for lower FPS
PERSISTENCE_FRAMES = 1  # Reduced from 2 for faster response (no filtering)
MAX_TRACKING_DISTANCE = 50  # Reduced for smaller resolution

# Audio settings
TTS_ENABLED = True
TTS_RATE = 175
MESSAGE_COOLDOWN = 8.0  # Increased to reduce CPU usage on TTS
GLOBAL_COOLDOWN = 3.0  # Increased from 2s
MAX_ANNOUNCE_OBJECTS = 2  # Reduced from 3

# Performance settings
SKIP_FRAMES = 3  # Process every 3rd frame (increased from 2)
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
# Ultrasonic sensor settings
ULTRASONIC_ENABLED = True  # Enable ultrasonic sensor
ULTRASONIC_CRITICAL_DISTANCE = 2.0  # meters - trigger critical alert
ULTRASONIC_WARNING_DISTANCE = 3.0   # meters - trigger warning

# WebSocket settings for mobile app
WEBSOCKET_ENABLED = True
WEBSOCKET_HOST = "0.0.0.0"  # Listen on all network interfaces
WEBSOCKET_PORT = 8765
