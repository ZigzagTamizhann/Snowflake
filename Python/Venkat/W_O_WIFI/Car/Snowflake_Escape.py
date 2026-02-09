import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Subu # type: ignore

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed=0.5, turn_speed=0.5):
        """Initializes the motor driver pins using PWM for speed control."""
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)

        self.set_speed(speed, turn_speed)
        self.stop()

    def set_speed(self, speed, turn_speed):
        """Sets motor speeds. speed is a value between 0.0 and 1.0."""
        self.duty_cycle = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_duty_cycle = int(max(0.0, min(1.0, turn_speed)) * 65535)

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

# --- Hardware Initialization ---
motor = Motor(a1_pin=Subu.IO17, a2_pin=Subu.IO18, b1_pin=Subu.IO19, b2_pin=Subu.IO20, speed=0.4, turn_speed=0.6)
ir_sensor = IRSensor(left_pin=Subu.IO15, right_pin=Subu.IO13)
ultrasonic = Ultrasonic(trigger_pin=Subu.IO12, echo_pin=Subu.IO11)
led = LED(num_leds=9)

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

       
        if distance < FOLLOW_DISTANCE_MIN_CM:
            print("Object too close. Stopping.")
            motor.set_speed(1.0, 0.6)
            motor.backward()
            led.set_all(255, 0, 0) 

        
        elif distance < FOLLOW_DISTANCE_MAX_CM:
            print("Object ahead. Moving forward.")
            motor.set_speed(0.4, 0.6) 
            led.set_all(0, 255, 0)  
            motor.backward()
                
        elif left_val == 0 and right_val == 1: 
            print("Object on the left. Turning left.")
            led.set_all(255, 150, 0) 
            motor.turn_left()
            
        elif left_val == 1 and right_val == 0: 
            print("Object on the right. Turning right.")
            led.set_all(255, 150, 0) 
            motor.turn_right()
            
        elif left_val == 0 and right_val == 0:
            print("Object on the both Side")
            led.set_all(255, 255, 0) 
            motor.turn_left()
            time.sleep_ms(100)
            motor.turn_right()
            time.sleep_ms(100)
            
            
        else:
            
            print("Object lost or too far. Waiting.")
            motor.stop()
            led.set_all(0, 0, 255) # Blue for waiting

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program stopped by user.")
    motor.stop()
    led.off()

                                                                            



