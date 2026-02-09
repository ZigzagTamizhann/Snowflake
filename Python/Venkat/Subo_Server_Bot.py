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
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, Turn, led_ctrl=None):
        """Initializes the motor driver pins using PWM for speed control."""
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))
        self.led_ctrl = led_ctrl

        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)

        self.set_speed(speed, Turn)
        self.stop()

    def set_speed(self, speed, Turn):
        """Sets motor speeds. speed is a value between 0.0 and 1.0."""
        self.duty_cycle = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_duty_cycle = int(max(0.0, min(1.0, Turn)) * 65535)

    def forward(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_FORWARD, (0, 255, 0))
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        """Moves the robot backward."""
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_BACKWARD, (255, 0, 0))
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_LEFT, (255, 255, 0))
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle); self.motor_b2.duty_u16(0)

    def turn_right(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ARROW_RIGHT, (255, 255, 0))
        self.motor_a1.duty_u16(self.turn_duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty_cycle)

    def stop(self):
        if self.led_ctrl: self.led_ctrl.display_icon(ICON_STOP, (255, 0, 0))
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)


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
Turn = 0.4

left_pin = Subu.IO1
right_pin = Subu.IO4

num_leds = 48

led = LED(num_leds)
motor = Motor(In1, In2, In3, In4, speed, Turn, led)
ir_sensor = IRSensor(left_pin, right_pin)

led.off()
   
print("Line Following Robot - Starting...")

# --- Main Program Loop ---
try:
    
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

    while True:
        
        left_val, right_val = ir_sensor.read_line() # type: ignore
        
        print(f"Sensor values: Left={left_val}, Right={right_val}")

        # --- Line Following Logic ---

        # Case 1: Both sensors on white surface -> Move forward
        if left_val == 0 and right_val == 0:
            print("Forward") # Green # type: ignore
            motor.forward()

        # Case 2: Right sensor on black line -> Turn right
        elif left_val == 0 and right_val == 1:
            print("Turn Left") # Yellow # type: ignore
            motor.turn_left()
            time.sleep_ms(50)
        
        # Case 3: Left sensor on black line -> Turn left
        elif left_val == 1 and right_val == 0:
            print("Turn Right")  # Yellow # type: ignore
            motor.turn_right()
            time.sleep_ms(100)

        # Case 4: Both sensors on black line (e.g., intersection or end) -> Stop
        elif left_val == 1 and right_val == 1:
            print("Line end or intersection. Stopping.")
            motor.stop()
            time.sleep_ms(5000)
            motor.forward()
            time.sleep_ms(100)

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program stopped by user.")
    # Cleanly stop motors and turn off LEDs
    led.off() # type: ignore
    motor.stop()
