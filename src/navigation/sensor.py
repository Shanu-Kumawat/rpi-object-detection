# ------------------------------------------------------------------------------
# Ultrasonic Sensor Module (HC-SR04)
# ------------------------------------------------------------------------------
# Measures distance using GPIO pins on Raspberry Pi
# ------------------------------------------------------------------------------

import time
from typing import Optional

# Try to import RPi.GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


class UltrasonicSensor:
    """HC-SR04 Ultrasonic distance sensor"""
    
    # GPIO pins (BCM numbering)
    TRIG_PIN = 17  # Physical pin 11
    ECHO_PIN = 27  # Physical pin 13
    
    # Timing constants
    TRIG_PULSE_DURATION = 0.00001  # 10 microseconds
    MAX_DISTANCE = 4.0  # Maximum reliable distance in meters
    TIMEOUT = 0.04  # 40ms timeout (corresponds to ~6.8m)
    
    def __init__(self, enabled: bool = True, trig_pin: int = None, echo_pin: int = None):
        """
        Initialize ultrasonic sensor
        
        Args:
            enabled: Enable sensor (False for testing without hardware)
            trig_pin: GPIO pin for trigger (BCM numbering)
            echo_pin: GPIO pin for echo (BCM numbering)
        """
        self.enabled = enabled and GPIO_AVAILABLE
        self.trig_pin = trig_pin or self.TRIG_PIN
        self.echo_pin = echo_pin or self.ECHO_PIN
        self.last_distance = None
        self.last_read_time = 0
        
        if self.enabled:
            self._setup_gpio()
            print(f"UltrasonicSensor initialized (TRIG: GPIO{self.trig_pin}, ECHO: GPIO{self.echo_pin})")
        else:
            if not GPIO_AVAILABLE:
                print("UltrasonicSensor disabled (RPi.GPIO not available)")
            else:
                print("UltrasonicSensor disabled (manual)")
    
    def _setup_gpio(self):
        """Setup GPIO pins"""
        try:
            # Set GPIO mode to BCM
            GPIO.setmode(GPIO.BCM)
            
            # Disable warnings
            GPIO.setwarnings(False)
            
            # Setup pins
            GPIO.setup(self.trig_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            
            # Ensure trigger is low
            GPIO.output(self.trig_pin, False)
            time.sleep(0.1)  # Let sensor settle
            
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            self.enabled = False
    
    def read_distance(self) -> Optional[float]:
        """
        Read distance from ultrasonic sensor
        
        Returns:
            Distance in meters, or None if reading failed
        """
        if not self.enabled:
            return None
        
        try:
            # Send trigger pulse
            GPIO.output(self.trig_pin, True)
            time.sleep(self.TRIG_PULSE_DURATION)
            GPIO.output(self.trig_pin, False)
            
            # Wait for echo start
            timeout_start = time.time()
            pulse_start = timeout_start
            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout_start > self.TIMEOUT:
                    return None  # Timeout
            
            # Wait for echo end
            timeout_start = time.time()
            pulse_end = pulse_start
            while GPIO.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end - timeout_start > self.TIMEOUT:
                    return None  # Timeout
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            
            # Speed of sound: 343 m/s at 20°C
            # Distance = (Time × Speed) / 2
            distance = (pulse_duration * 343) / 2
            
            # Validate reading
            if distance > self.MAX_DISTANCE or distance < 0.02:  # Min 2cm
                return None  # Out of range
            
            self.last_distance = distance
            self.last_read_time = time.time()
            
            return distance
            
        except Exception as e:
            print(f"Error reading ultrasonic sensor: {e}")
            return None
    
    def get_average_distance(self, samples: int = 3) -> Optional[float]:
        """
        Get average distance from multiple samples
        
        Args:
            samples: Number of samples to average
            
        Returns:
            Average distance in meters, or None if failed
        """
        if not self.enabled:
            return None
        
        readings = []
        for _ in range(samples):
            distance = self.read_distance()
            if distance is not None:
                readings.append(distance)
            time.sleep(0.01)  # Small delay between readings (10ms)
        
        if not readings:
            return None
        
        return sum(readings) / len(readings)
    
    def get_status(self) -> str:
        """
        Get human-readable status
        
        Returns:
            Status string
        """
        if not self.enabled:
            return "disabled"
        
        if self.last_distance is None:
            return "no reading"
        elif self.last_distance < 1.0:
            return "obstacle close"
        elif self.last_distance < 2.0:
            return "obstacle near"
        else:
            return "clear"
    
    def is_obstacle_detected(self, critical_distance: float = 1.0) -> bool:
        """
        Check if obstacle is within critical distance
        
        Args:
            critical_distance: Distance threshold in meters
            
        Returns:
            True if obstacle detected within threshold
        """
        if not self.enabled or self.last_distance is None:
            return False
        
        return self.last_distance < critical_distance
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.enabled and GPIO_AVAILABLE:
            try:
                GPIO.cleanup([self.trig_pin, self.echo_pin])
            except:
                pass


# Test function
def test_sensor():
    """Test ultrasonic sensor"""
    print("Testing Ultrasonic Sensor (HC-SR04)")
    print("Press Ctrl+C to stop\n")
    
    sensor = UltrasonicSensor(enabled=True)
    
    if not sensor.enabled:
        print("Sensor not available!")
        return
    
    try:
        while True:
            distance = sensor.get_average_distance(samples=5)
            
            if distance is not None:
                print(f"Distance: {distance:.2f} m ({distance * 100:.1f} cm)")
                
                # Alert if too close
                if distance < 2.0:
                    print("  ⚠️  ALERT: Object within 2 meters!")
                elif distance < 3.0:
                    print("  ⚡ WARNING: Object within 3 meters")
            else:
                print("No object detected (out of range)")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nTest stopped")
    
    finally:
        sensor.cleanup()
        print("Cleanup complete")


if __name__ == '__main__':
    test_sensor()

