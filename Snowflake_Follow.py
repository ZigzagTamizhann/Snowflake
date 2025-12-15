import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Snowflake # type: ignore

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed=0.5, turn_speed=0.8):
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
        # Assuming 0 means detection (obstacle is near)
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
            # Measure the pulse duration on the echo pin
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
            Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(a1_pin=Snowflake.IO17, a2_pin=Snowflake.IO18, b1_pin=Snowflake.IO19, b2_pin=Snowflake.IO20, speed=0.4, turn_speed=0.6)
ir_sensor = IRSensor(left_pin=Snowflake.IO15, right_pin=Snowflake.IO13)
ultrasonic = Ultrasonic(trigger_pin=Snowflake.IO11, echo_pin=Snowflake.IO12)
led = LED(num_leds=9)

# --- Configuration ---
FOLLOW_DISTANCE_MAX_CM = 30  # இந்த தூரத்திற்குள் கண்டறிந்தால் பின்தொடர ஆரம்பிக்கும்
FOLLOW_DISTANCE_MIN_CM = 10  # இந்த தூரத்தை அடைந்ததும் நின்றுவிடும்

print("Follow Me Robot - Starting...")

try:
    # Startup LED sequence
    for i in range(1, led.NUM_LEDS + 1):
        Snowflake.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep(1)
    led.off()

    while True:
        distance = ultrasonic.distance_cm()
        # Assuming IR sensor returns 0 for detection, 1 for no detection
        left_val, right_val = ir_sensor.read_values()

        print(f"Distance: {distance:.1f} cm, IR: L={left_val} R={right_val}")

        # விதி 1: பொருள் மிக அருகில் இருந்தால் (10 செ.மீ.க்குள்), நின்றுவிடும்.
        if distance < FOLLOW_DISTANCE_MIN_CM:
            print("Object too close. Stopping.")
            motor.set_speed(1.0, 0.6) # வேகத்தை முழுமையாக்குகிறது
            motor.backward()
            led.set_all(255, 0, 0) # Red for stop

        # விதி 2: பொருள் பின்தொடரும் தூரத்தில் இருந்தால் (10-30 செ.மீ.), பின்தொடரவும்.
        elif distance < FOLLOW_DISTANCE_MAX_CM:
            print("Object ahead. Moving forward.")
            motor.set_speed(0.4, 0.6) # சாதாரண வேகத்திற்கு திரும்புகிறது
            led.set_all(0, 255, 0)  # Green for following
            motor.forward()
                
        elif left_val == 0 and right_val == 1: # இடது IR மட்டும் கண்டறிந்தால்
            print("Object on the left. Turning left.")
            led.set_all(255, 150, 0)  # Orange for turning
            motor.turn_right()
            
        elif left_val == 1 and right_val == 0: # வலது IR மட்டும் கண்டறிந்தால்
            print("Object on the right. Turning right.")
            led.set_all(255, 150, 0)  # Orange for turning
            motor.turn_left()
            
        elif left_val == 0 and right_val == 0:
            print("Object on the both Side")
            led.set_all(255, 255, 0)  # Orange for turning
            motor.turn_left()
            time.sleep_ms(100) # Loop delay
            motor.turn_right()
            time.sleep_ms(100) # Loop delay
            
            
        else:
            # விதி 3: பொருள் தொலைவில் இருந்தால் (30 செ.மீ.க்கு மேல்), நின்றுவிடும்.
            print("Object lost or too far. Waiting.")
            motor.stop()
            led.set_all(0, 0, 255) # Blue for waiting

        time.sleep_ms(50) # Loop delay

except KeyboardInterrupt:
    print("Program stopped by user.")
    motor.stop()
    led.off()

                                                                            
