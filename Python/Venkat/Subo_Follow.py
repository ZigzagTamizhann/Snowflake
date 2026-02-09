import time
from machine import Pin, PWM, time_pulse_us # type: ignore
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
        self.left_ir_pin = Pin(left_pin, Pin.IN)
        self.right_ir_pin = Pin(right_pin, Pin.IN)

    def read_values(self):
        
        return (self.left_ir_pin.value(), self.right_ir_pin.value())

class Ultrasonic:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            
            pulse_duration = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout
            distance = (pulse_duration * 0.0343) / 2
            return distance
        except OSError:
            return float('inf')

class LED:
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
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

Trig = Subu.IO2
Echo = Subu.IO3

led = LED(num_leds)
motor = Motor(In1, In2, In3, In4, speed, Turn, led)
ir_sensor = IRSensor(left_pin, right_pin)

led.off()
ultrasonic = Ultrasonic(Trig, Echo)

# --- Configuration ---
FOLLOW_DISTANCE_MAX_CM = 30  
FOLLOW_DISTANCE_MIN_CM = 10  

print("Follow Me Robot - Starting...")

try:
    
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep(1)
    led.off()

    while True:
        distance = ultrasonic.distance_cm()
        
        left_val, right_val = ir_sensor.read_values()

        print(f"Distance: {distance:.1f} cm, IR: L={left_val} R={right_val}")

       
        if distance < FOLLOW_DISTANCE_MIN_CM and distance > 0:
            print("Object too close. Stopping.")
            motor.set_speed(1.0, 0.6)
            motor.backward()

        
        elif distance < FOLLOW_DISTANCE_MAX_CM and distance > FOLLOW_DISTANCE_MIN_CM:
            print("Object ahead. Moving forward.")
            motor.set_speed(0.4, 0.6) 
            motor.forward()
                
        elif left_val == 0 and right_val == 1: 
            print("Object on the left. Turning left.")
            motor.turn_left()
            
        elif left_val == 1 and right_val == 0: 
            print("Object on the right. Turning right.")
            motor.turn_right()
            
        elif left_val == 0 and right_val == 0:
            print("Object on the both Side")
            motor.turn_left()
            time.sleep_ms(100)
            motor.turn_right()
            time.sleep_ms(100)
            
            
        else:
            
            print("Object lost or too far. Waiting.")
            motor.stop()

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program stopped by user.")
    motor.stop()
    led.off()

                                                                            
