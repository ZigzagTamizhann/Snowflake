import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore
import random

# --- Icon Definitions ---
ARROW_FORWARD = [0b00011000, 0b00111100, 0b01111110, 0b00011000, 0b00011000, 0b00011000]
ARROW_BACKWARD = [0b00011000, 0b00011000, 0b00011000, 0b01111110, 0b00111100, 0b00011000]
ARROW_LEFT = [0b00011000, 0b00111000, 0b11111111, 0b11111111, 0b00111000, 0b00011000]
ARROW_RIGHT = [0b00011000, 0b00011100, 0b11111111, 0b11111111, 0b00011100, 0b00011000]
ICON_STOP = [0b00111100, 0b01100010, 0b10010001, 0b10001001, 0b01000110, 0b00111100]

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, Turn):
        """Initializes the motor driver pins using PWM for speed control."""
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

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
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        """Moves the robot backward."""
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

class IRSensor:
    def __init__(self, fl_pin, fr_pin, bl_pin, br_pin):
        self.fl = Pin(fl_pin, Pin.IN)
        self.fr = Pin(fr_pin, Pin.IN)
        self.bl = Pin(bl_pin, Pin.IN)
        self.br = Pin(br_pin, Pin.IN)

    def read_all(self):
        return (self.fl.value(), self.fr.value(), self.bl.value(), self.br.value())

class LED:
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def display_icon(self, icon_data, color):
        """Displays a 6-row bitmap on the Subu LED matrix."""
        self.off()
        # This assumes your Subu LED matrix maps linearly 
        # to the binary bits provided in the template.
        idx = 1
        for row in icon_data:
            for bit in range(8):
                if (row >> (7 - bit)) & 1:
                    if idx <= self.NUM_LEDS:
                        Subu.setSingleLED(idx, color)
                idx += 1

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
In1 = Subu.IO18
In2 = Subu.IO19
In3 = Subu.IO20
In4 = Subu.IO21

speed = 0.4
Turn = 0.4

Front_left_pin = Subu.IO1
Front_right_pin = Subu.IO4
Back_Left_pin = Subu.IO2
Back_Right_pin = Subu.IO3

num_leds = 48

motor = Motor(In1, In2, In3, In4, speed, Turn)
led = LED(num_leds)
ir_sensor = IRSensor(Front_left_pin, Front_right_pin, Back_Left_pin, Back_Right_pin)

def safe_delay_backward(ms):
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        _, _, bl, br = ir_sensor.read_all()
        if bl == 1 or br == 1:
            motor.stop()
            return False 
        time.sleep_ms(10)
    return True

print("Robot with LED Arrows - Starting...")

try:
    led.off()
    while True:
        fl, fr, bl, br = ir_sensor.read_all()
        
        if fl == 0 and fr == 0:
            motor.forward()
        else:
            print("Edge! Avoidance maneuver...")
            motor.backward()
            if safe_delay_backward(1000):
                motor.stop()
                time.sleep_ms(200)
                if random.choice([0, 1]) == 0:
                    motor.turn_left()
                else:
                    motor.turn_right()
                time.sleep_ms(800)
                motor.stop()
            else:
                motor.stop()
                time.sleep_ms(1000)

        time.sleep_ms(10)

except KeyboardInterrupt:
    led.off()
    motor.stop()