import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Snowflake # type: ignore
import random
# import ir_sensor # You can uncomment this when you add code to ir_sensor.py
class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed = 0.5):
        """Initializes the motor driver pins using PWM for speed control."""
        # Initialize pins as PWM objects
        self.motor_a1 = PWM(a1_pin)
        self.motor_a2 = PWM(a2_pin)
        self.motor_b1 = PWM(b1_pin)
        self.motor_b2 = PWM(b2_pin)

        # Set a common frequency for all motor PWM pins
        freq = 1000
        self.motor_a1.freq(freq)
        self.motor_a2.freq(freq)
        self.motor_b1.freq(freq)
        self.motor_b2.freq(freq)

        # Set the speed (duty cycle)
        self.set_speed(speed)

        self.stop()

    def set_speed(self, speed):
        """Sets motor speed. speed is a value between 0.0 and 1.0."""
        speed = max(0.0, min(1.0, speed)) # Clamp speed between 0 and 1
        self.duty_cycle = int(speed * 65535)
        
        # Set a separate, max-speed duty cycle for turning
        self.turn_duty_cycle = int(0.4 * 65535)

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle)
        self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        self.motor_a1.duty_u16(self.turn_duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.turn_duty_cycle)

    def turn_right(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle)
        self.motor_b2.duty_u16(0)

    def stop(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)

class Ultrasonic:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trig_pin, echo_pin):
        self.trigger = trig_pin
        self.echo = echo_pin

    def get_distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout
            if pulse_duration < 0:
                return -1
            distance = (pulse_duration * 0.0343) / 2
            return distance
        except OSError:
            return -1

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1): Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Main Program ---
# --- Pin Definitions ---
# Define all hardware pins here for easy configuration.

# Motor A (Left) Pins
motor_a1_pin = Pin(Snowflake.IO17, Pin.OUT)
motor_a2_pin = Pin(Snowflake.IO18, Pin.OUT)

# Motor B (Right) Pins  
motor_b1_pin = Pin(Snowflake.IO19, Pin.OUT)
motor_b2_pin = Pin(Snowflake.IO20, Pin.OUT)

# Ultrasonic Sensor Pins
ultrasonic_trigger = Pin(Snowflake.IO12, Pin.OUT)
ultrasonic_echo = Pin(Snowflake.IO11, Pin.IN)

# --- Initialize Modules with Pins ---
motor_controller = Motor(a1_pin=motor_a1_pin, a2_pin=motor_a2_pin, b1_pin=motor_b1_pin, b2_pin=motor_b2_pin, speed=0.4)
ultrasonic = Ultrasonic(trig_pin=ultrasonic_trigger, echo_pin=ultrasonic_echo)
led = LED(num_leds=9)

OBSTACLE_DISTANCE_CM = 20

print("Obstacle Avoiding Car - Starting...")

try:
    # Startup LED sequence
    for i in range(1, led.NUM_LEDS + 1):
        Snowflake.setSingleLED(i, (0, 0, 255)) # Blue
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

    while True:
        distance = ultrasonic.get_distance_cm()
        # Print the measured distance
        if distance != -1:
            print(f"Distance: {distance:.1f} cm")
        else:
            print("Distance: Timeout")

        if distance != -1 and distance < OBSTACLE_DISTANCE_CM:
            print("Obstacle detected! Avoiding...")
            # Obstacle Detected: Set LEDs to red
            led.set_all(255, 0, 0) # Red
            motor_controller.stop()
            time.sleep_ms(100)
            
            print("Reversing...")
            # Reversing: Set LEDs to yellow
            led.set_all(255, 150, 0) # Yellow
            motor_controller.backward()
            time.sleep_ms(500)
            
            # Randomly choose to turn left or right
            if random.choice([0, 1]) == 0:
                print("Turning left randomly...")
                motor_controller.turn_left()
            else:
                print("Turning right randomly...")
                motor_controller.turn_right()

            time.sleep_ms(700)
            
            motor_controller.stop()
            time.sleep_ms(100)
        else:
            print("Moving forward...")
            # No obstacle, moving forward: Set LEDs to green
            led.set_all(0, 255, 0) # Green
            motor_controller.forward()

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program stopped.")
    # Cleanly stop motors and turn off LEDs
    led.off()
    motor_controller.stop()
