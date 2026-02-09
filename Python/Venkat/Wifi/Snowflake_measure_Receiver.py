import time
from machine import Pin, PWM, UART, time_pulse_us # type: ignore
import Snowflake # type: ignore

# --- Hardware Abstraction Classes ---
class Ultrasonic:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
    def get_distance_cm(self):
        """Returns the distance in centimeters."""
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            # time_pulse_us returns the pulse duration in microseconds
            pulse_duration = time_pulse_us(self.echo, 1, 30000) # 30ms timeout
            # Calculate distance: (duration * speed_of_sound) / 2
            # Speed of sound = 343 m/s or 0.0343 cm/us
            distance = (pulse_duration * 0.0343) / 2
            return distance
        except OSError:
            # This can happen if the echo pulse is not received within the timeout
            return -1

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, initial_speed=0.5):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)

        self.set_speed(initial_speed)
        self.stop()
    def set_speed(self, speed_fraction):
        """Sets motor speed. speed_fraction is a value between 0.0 and 1.0."""
        speed_fraction = max(0.2, min(1.0, speed_fraction))
        self.duty_cycle = int(speed_fraction * 65535)
        self.turn_duty_cycle = int(min(1.0, speed_fraction * 1.2) * 65535)
        print(f"Speed set to {int(speed_fraction * 100)}%")

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle); self.motor_b2.duty_u16(0)

    def turn_right(self):
        self.motor_a1.duty_u16(self.turn_duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty_cycle)

    def stop(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds=9):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware and Communication Setup ---
motor = Motor(
    a1_pin=Snowflake.IO3, a2_pin=Snowflake.IO4,
    b1_pin=Snowflake.IO5, b2_pin=Snowflake.IO6,
    initial_speed=0.5
)
led = LED()

# IMPORTANT: Connect the ultrasonic sensor to these pins on the receiver board
ultrasonic = Ultrasonic(trigger_pin=Snowflake.IO9, echo_pin=Snowflake.IO10)

# Configure UART to send commands to the other ESP32.
# Connect this board's TX pin (IO1) to the web server ESP32's RX pin (Cayo.IO10).
# Connect this board's RX pin (IO2) to the web server ESP32's TX pin (Cayo.IO9).
uart = UART(0, baudrate=115200, tx=Snowflake.IO1, rx=Snowflake.IO2)

print("Snowflake Command Receiver: Ready for commands.")
led.set_all(0, 0, 255) # Blue to indicate startup
time.sleep(1)
led.off()
 
# --- Automatic Movement Function ---
def move_to_distance(target_distance_cm):
    """
    Moves the robot to a specific distance from an object, deciding direction automatically.
    - target_distance_cm: The goal distance in cm.
    """
    print(f"Auto mode: Moving to target distance of {target_distance_cm} cm.")
    led.set_all(255, 0, 255) # Magenta for auto mode

    # Proportional control constants (these may need tuning)
    KP = 0.08  # Proportional gain - determines how aggressively the robot reacts to error.
    MIN_SPEED = 0.25 # Minimum speed to prevent stalling
    MAX_SPEED = 0.8  # Maximum speed
    TOLERANCE = 1.0  # How close is "close enough" (in cm)

    while True:
        current_distance = ultrasonic.get_distance_cm()
        if current_distance < 0: # Invalid reading
            print("Invalid sensor reading, stopping.")
            motor.stop()
            led.set_all(255, 0, 0) # Red for error
            return

        error = current_distance - target_distance_cm
        print(f"Target: {target_distance_cm}, Current: {current_distance:.1f}, Error: {error:.1f}")

        # Check if we have reached the target
        if abs(error) <= TOLERANCE:
            print("Target reached.")
            motor.stop()
            led.set_all(0, 255, 255) # Cyan for success
            time.sleep(2) # Show success color
            led.off()
            return

        # Calculate speed based on error
        speed = abs(error) * KP
        speed = max(MIN_SPEED, min(MAX_SPEED, speed)) # Clamp speed to valid range
        motor.set_speed(speed)

        # Automatically decide direction based on the error
        if error > 0: # Current distance is greater than target, so move forward
            motor.forward()
        else: # Current distance is less than target, so move backward
            motor.backward()
        
        # Check for manual override command
        if uart.any():
            print("Manual override received, stopping auto mode.")
            break
        time.sleep_ms(50)

# --- Main Program Loop ---
while True:
    try:
        distance = ultrasonic.get_distance_cm()
        
        # Format the data as a simple string and send it over UART
        # The newline character '\n' is important to mark the end of a message.
        uart.write(f"{distance:.1f}\n")
        print(f"Sent distance: {distance:.1f} cm")

        if uart.any():
            command_bytes = uart.readline()
            if not command_bytes:
                continue

            command = command_bytes.decode('utf-8').strip()
            print(f"Received: '{command}'")

            # --- Command Processing ---
            if command == 'F':
                led.set_all(0, 255, 0) # Green for forward
                motor.forward()
            elif command == 'B':
                led.set_all(255, 100, 0) # Orange for backward
                motor.backward()
            elif command == 'L':
                led.set_all(0, 0, 255) # Blue for left
                motor.turn_left()
            elif command == 'R':
                led.set_all(0, 0, 255) # Blue for right
                motor.turn_right()
            elif command == 'S':
                led.set_all(255, 0, 0) 
                motor.stop()
            elif command.startswith('V'):
                try:
                    # Extract speed value (e.g., from 'V50')
                    speed_percent = int(command[1:])
                    speed_fraction = speed_percent / 100.0
                    motor.set_speed(speed_fraction)
                except (ValueError, IndexError):
                    print("Invalid speed command received.")
            elif command.startswith('A'): # Automatic movement command (e.g., 'AF20' or 'AB15')
                try: # e.g., 'A20'
                    distance_val = int(command[1:])
                    move_to_distance(distance_val)
                except (ValueError, IndexError):
                    print("Invalid auto command received.")
                led.off() # Turn off LED after auto mode finishes

        time.sleep_ms(200) # Send data 5 times per second

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(1)
