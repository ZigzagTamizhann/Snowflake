import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed):
        """Initializes the motor driver pins using PWM for speed control."""
        # Initialize pins as PWM objects
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

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
        self.turn_duty_cycle = int(0.8 * 65535)

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

class IRSensor:
    def __init__(self, left_pin, right_pin):
        """Initializes the IR sensor pins."""
        self.left_ir_pin = Pin(left_pin, Pin.IN)
        self.right_ir_pin = Pin(right_pin, Pin.IN)

    def read_line(self):
        """
        Reads the state of the left and right IR sensors.
        Returns a tuple (left_value, right_value).
        Typically, 0 means a black line is detected, and 1 means a white surface.
        """
        return (self.left_ir_pin.value(), self.right_ir_pin.value())

class LED:
    def __init__(self, num_leds):
        """Initializes the LED strip."""
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        """Sets all LEDs to the same color."""
        for i in range(1, self.NUM_LEDS + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
        """Turns all LEDs off."""
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(a1_pin=Subu.IO18, a2_pin=Subu.IO19, b1_pin=Subu.IO20, b2_pin=Subu.IO21, speed=0.40)
ir_sensor = IRSensor(left_pin=Subu.IO1, right_pin=Subu.IO4)
led = LED(num_leds=48)
   
print("Rope Car - Moving Forward...")

# --- Main Program Loop ---
moving_forward = True # Start by moving forward

try:
    while True:
        # Read sensor values
        left_val, right_val = ir_sensor.read_line()
        print(f"Left IR: {left_val}, Right IR: {right_val}") # Assuming 0 is detection

        # If left sensor detects, set direction to backward
        if right_val == 0:
            moving_forward = False
        # If right sensor detects, set direction to forward
        elif left_val == 0:
            moving_forward = True

        # Move the robot based on the current direction state
        if moving_forward:
            print("Direction: Forward")
            motor.forward()
        else:
            print("Direction: Backward")
            motor.backward()

        time.sleep_ms(100) # Increased delay to make printing readable

except KeyboardInterrupt:
    print("Program stopped by user.")
    # Cleanly stop motors and turn off LEDs
    motor.stop()
    led.off()
    print("Robot has stopped.")
