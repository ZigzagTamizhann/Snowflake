import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore

# --- Icon Definitions ---
ARROW_FORWARD = [0b00011000, 0b00111100, 0b01111110, 0b00011000, 0b00011000, 0b00011000]
ARROW_BACKWARD = [0b00011000, 0b00011000, 0b00011000, 0b01111110, 0b00111100, 0b00011000]
ARROW_LEFT = [0b00011000, 0b00111000, 0b11111111, 0b11111111, 0b00111000, 0b00011000]
ARROW_RIGHT = [0b00011000, 0b00011100, 0b11111111, 0b11111111, 0b00011100, 0b00011000]
ICON_STOP = [0b00111100, 0b01100010, 0b10010001, 0b10001001, 0b01000110, 0b00111100]

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, led_ctrl=None):
        """Initializes the motor driver pins using PWM for speed control."""
        # Initialize pins as PWM objects
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))
        self.led_ctrl = led_ctrl

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
        
    def forward(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_FORWARD, (0, 255, 0))
        self.motor_a1.duty_u16(self.duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle)
        self.motor_b2.duty_u16(0)

    def backward(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_BACKWARD, (255, 0, 0))
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.duty_cycle)

    def stop(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ICON_STOP, (255, 0, 0))
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

    def display_icon(self, icon_data, color):
        """Displays a 6-row bitmap on the Subu LED matrix."""
        self.off()
        idx = 1
        for row in icon_data:
            for bit in range(8):
                if (row >> (7 - bit)) & 1:
                    if idx <= self.NUM_LEDS:
                        Subu.setSingleLED(idx, color)
                idx += 1

# --- Hardware Initialization ---
In1 = Subu.IO18
In2 = Subu.IO19
In3 = Subu.IO20
In4 = Subu.IO21

speed = 0.4

left_pin = Subu.IO1
right_pin = Subu.IO4

num_leds = 48

led = LED(num_leds)
motor = Motor(In1, In2, In3, In4, speed, led)
ir_sensor = IRSensor(left_pin, right_pin)

   
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
