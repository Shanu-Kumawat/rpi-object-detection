#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# Navigation System Main Runner
# ------------------------------------------------------------------------------
# Main application for visually impaired navigation using YOLO + zones + TTS
# ------------------------------------------------------------------------------

import cv2
import sys
import time
import argparse
from typing import Optional

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from . import config
from .detector import ObjectDetector
from .zone_mapper import ZoneMapper
from .announcer import AudioAnnouncer
from .sensor import UltrasonicSensor
from .websocket_server import NavigationWebSocketServer


class NavigationSystem:
    """Main navigation system coordinator"""
    
    def __init__(self, 
                 camera_id: int = 0,
                 model_path: str = None,
                 enable_tts: bool = True,
                 show_video: bool = True):
        """
        Initialize navigation system
        
        Args:
            camera_id: Camera device ID
            model_path: Path to YOLO model
            enable_tts: Enable text-to-speech
            show_video: Show video window with detections
        """
        self.camera_id = camera_id
        self.show_video = show_video
        
        print("=" * 60)
        print("NAVIGATION SYSTEM FOR VISUALLY IMPAIRED")
        print("=" * 60)
        
        # Initialize camera
        print(f"\nInitializing camera {camera_id}...")
        self.use_picamera2 = PICAMERA2_AVAILABLE
        
        if self.use_picamera2:
            # Use Picamera2 for Raspberry Pi
            self.cap = Picamera2()
            camera_config = self.cap.create_preview_configuration(
                main={"size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT), "format": "RGB888"}
            )
            self.cap.configure(camera_config)
            self.cap.start()
            actual_width = config.CAMERA_WIDTH
            actual_height = config.CAMERA_HEIGHT
            print(f"Camera opened: {actual_width}x{actual_height}")
        else:
            # Fallback to OpenCV VideoCapture
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {camera_id}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Camera opened: {actual_width}x{actual_height}")
        
        # Initialize components
        print("\nInitializing detection system...")
        self.detector = ObjectDetector(model_path=model_path)
        self.zone_mapper = ZoneMapper(frame_width=actual_width)
        self.announcer = AudioAnnouncer(enabled=enable_tts)
        self.sensor = UltrasonicSensor(enabled=config.ULTRASONIC_ENABLED)
        
        # Initialize WebSocket server for mobile app
        self.ws_server = None
        if config.WEBSOCKET_ENABLED:
            self.ws_server = NavigationWebSocketServer(
                host=config.WEBSOCKET_HOST,
                port=config.WEBSOCKET_PORT
            )
            self.ws_server.start()
            time.sleep(0.5)  # Give server time to start
        
        # Stats
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_history = []
        
        print("\n" + "=" * 60)
        print("System ready! Press 'q' or ESC to quit")
        print("=" * 60 + "\n")
    
    def draw_zones(self, frame):
        """Draw zone boundaries on frame"""
        height, width = frame.shape[:2]
        
        # Zone boundaries
        left_x = int(self.zone_mapper.left_boundary)
        right_x = int(self.zone_mapper.right_boundary)
        
        # Draw vertical lines
        cv2.line(frame, (left_x, 0), (left_x, height), (255, 255, 0), 2)
        cv2.line(frame, (right_x, 0), (right_x, height), (255, 255, 0), 2)
        
        # Draw labels
        cv2.putText(frame, "LEFT", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, "CENTER", (left_x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, "RIGHT", (right_x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    def draw_detections(self, frame, zone_dict):
        """Draw bounding boxes and labels on frame"""
        # Colors for zones
        zone_colors = {
            'left': (255, 0, 0),    # Blue
            'center': (0, 255, 0),  # Green
            'right': (0, 0, 255),   # Red
        }
        
        for zone, detections in zone_dict.items():
            color = zone_colors.get(zone, (255, 255, 255))
            
            for zd in detections:
                det = zd.detection
                x1, y1, x2, y2 = det.bbox
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{det.class_name} ({det.confidence:.2f})"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(frame, (x1, y1 - label_size[1] - 4), (x1 + label_size[0], y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def process_frame(self, frame):
        """Process a single frame"""
        # Run detection
        detections, inference_time = self.detector.detect_with_timing(frame)
        
        # Map to zones and filter
        zone_dict = self.zone_mapper.process(detections)
        
        # Read ultrasonic distance
        ultrasonic_distance = None
        if self.sensor.enabled:
            ultrasonic_distance = self.sensor.get_average_distance(samples=3)
            if ultrasonic_distance is not None:
                print(f"📏 Ultrasonic: {ultrasonic_distance:.2f}m")  # Debug output
        
        # Extract front objects for better ultrasonic messages
        front_objects = []
        if 'center' in zone_dict and zone_dict['center']:
            # Sort by priority (already done by zone_mapper)
            front_objects = [zd.detection.class_name for zd in zone_dict['center'][:2]]
        
        # Generate message with ultrasonic integration
        message = None
        is_priority = False
        
        # Priority 1: Ultrasonic critical alert with object name
        if ultrasonic_distance is not None and ultrasonic_distance < config.ULTRASONIC_CRITICAL_DISTANCE:
            if front_objects:
                obj_name = front_objects[0]
                message = f"Stop! {obj_name} ahead at {ultrasonic_distance:.1f} meters"
            else:
                message = f"Stop! Obstacle ahead at {ultrasonic_distance:.1f} meters"
            is_priority = True
        
        # Priority 2: Ultrasonic warning with object name
        elif ultrasonic_distance is not None and ultrasonic_distance < config.ULTRASONIC_WARNING_DISTANCE:
            if front_objects:
                obj_name = front_objects[0]
                message = f"Warning: {obj_name} in front at {ultrasonic_distance:.1f} meters"
            else:
                message = f"Warning: Obstacle in front at {ultrasonic_distance:.1f} meters"
            is_priority = True
        
        # Priority 3: Regular zone-based announcements
        else:
            message = self.announcer.generate_message(zone_dict)
            is_priority = False
        
        # Announce message
        if message:
            self.announcer.announce(message, priority=is_priority)
        
        # Send WebSocket alerts to mobile app
        if self.ws_server and self.ws_server.running:
            if ultrasonic_distance is not None and ultrasonic_distance < config.ULTRASONIC_CRITICAL_DISTANCE:
                obj_name = front_objects[0] if front_objects else "obstacle"
                print(f"📱 Sending CRITICAL alert to app: {obj_name} at {ultrasonic_distance:.2f}m")
                self.ws_server.broadcast_alert_sync(
                    "critical",
                    message if message else f"Critical: {obj_name}",
                    distance=ultrasonic_distance,
                    object_name=obj_name
                )
            elif ultrasonic_distance is not None and ultrasonic_distance < config.ULTRASONIC_WARNING_DISTANCE:
                obj_name = front_objects[0] if front_objects else "obstacle"
                print(f"📱 Sending WARNING alert to app: {obj_name} at {ultrasonic_distance:.2f}m")
                self.ws_server.broadcast_alert_sync(
                    "warning",
                    message if message else f"Warning: {obj_name}",
                    distance=ultrasonic_distance,
                    object_name=obj_name
                )
        
        # Update stats
        self.frame_count += 1
        
        return zone_dict, inference_time
    
    def run(self):
        """Main processing loop"""
        frame_counter = 0  # For frame skipping
        skip_frames = getattr(config, 'SKIP_FRAMES', 1)  # Process every Nth frame
        display_enabled = getattr(config, 'DISPLAY_ENABLED', True)
        stats_enabled = getattr(config, 'STATS_ENABLED', True)
        
        try:
            while True:
                # Read frame
                if self.use_picamera2:
                    frame = self.cap.capture_array()
                    ret = frame is not None
                else:
                    ret, frame = self.cap.read()
                
                if not ret:
                    print("Error: Failed to read frame")
                    break
                
                frame_counter += 1
                
                # Skip frames if configured (process every Nth frame)
                if frame_counter % skip_frames != 0:
                    if display_enabled and self.show_video:
                        cv2.imshow("Navigation System", frame)
                    if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
                        break
                    continue
                
                frame_start = time.time()
                
                # Process frame
                zone_dict, inference_time = self.process_frame(frame)
                
                # Calculate FPS
                frame_time = (time.time() - frame_start) * 1000
                fps = 1000 / frame_time if frame_time > 0 else 0
                self.fps_history.append(fps)
                if len(self.fps_history) > 30:
                    self.fps_history.pop(0)
                avg_fps = sum(self.fps_history) / len(self.fps_history)
                
                # Display video with annotations (only if enabled)
                if display_enabled and self.show_video:
                    display_frame = frame.copy()
                    self.draw_zones(display_frame)
                    self.draw_detections(display_frame, zone_dict)
                    
                    # Draw stats (if enabled)
                    if stats_enabled:
                        stats_text = [
                            f"FPS: {avg_fps:.1f}",
                            f"Inference: {inference_time:.1f}ms",
                            f"Frame: {frame_time:.1f}ms",
                            f"Detections: {sum(len(d) for d in zone_dict.values())}",
                        ]
                        
                        y_offset = frame.shape[0] - 20
                        for text in reversed(stats_text):
                            cv2.putText(display_frame, text, (10, y_offset), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            y_offset -= 20
                    
                    cv2.imshow("Navigation System", display_frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q or ESC
                    break
                elif key == ord('m'):  # Toggle mute
                    self.announcer.enabled = not self.announcer.enabled
                    status = "enabled" if self.announcer.enabled else "disabled"
                    print(f"Audio {status}")
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        
        # Print stats
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        print(f"\nSession statistics:")
        print(f"  Frames processed: {self.frame_count}")
        print(f"  Total time: {elapsed:.1f}s")
        print(f"  Average FPS: {avg_fps:.1f}")
        
        # Release resources
        if self.use_picamera2:
            self.cap.stop()
        else:
            self.cap.release()
        cv2.destroyAllWindows()
        self.announcer.stop()
        self.sensor.cleanup()
        if self.ws_server:
            self.ws_server.stop()
        
        print("Cleanup complete")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Navigation system for visually impaired users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python -m src.navigation.navigation_system
  
  # Use different camera
  python -m src.navigation.navigation_system --camera 1
  
  # Disable audio for testing
  python -m src.navigation.navigation_system --no-audio
  
  # Headless mode (no video window)
  python -m src.navigation.navigation_system --no-video

Controls:
  q or ESC  - Quit
  m         - Toggle mute/unmute audio
        """
    )
    
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--model', type=str, default=None,
                       help=f'Path to YOLO model (default: {config.YOLO_MODEL})')
    parser.add_argument('--no-audio', action='store_true',
                       help='Disable text-to-speech audio')
    parser.add_argument('--no-video', action='store_true',
                       help='Disable video window (headless mode)')
    
    args = parser.parse_args()
    
    try:
        nav_system = NavigationSystem(
            camera_id=args.camera,
            model_path=args.model,
            enable_tts=not args.no_audio,
            show_video=not args.no_video
        )
        nav_system.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
