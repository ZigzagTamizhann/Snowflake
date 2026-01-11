import time
from machine import Pin, PWM, time_pulse_us
import Snowflake

# ------------------ MOTOR CLASS ------------------ #
class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, turn_speed):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(1000)

        self.set_speed(speed, turn_speed)
        self.stop()

    def set_speed(self, speed, turn_speed):
        self.duty_cycle = int(max(0, min(1, speed)) * 65535)
        self.turn_duty_cycle = int(max(0, min(1, turn_speed)) * 65535)

    def forward(self):
        print("F")
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        print("B")
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self, t=1000):
        print("L")
        self.motor_a1.duty_u16(self.turn_duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty_cycle)
        time.sleep_ms(t)
        self.stop()

    def turn_right(self, t=1000):
        print("R")
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle); self.motor_b2.duty_u16(0)
        time.sleep_ms(t)
        self.stop()

    def stop(self):
        print("S")
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)

# ------------------ IR SENSOR ------------------ #
class IRSensor:
    def __init__(self, left_pin, right_pin):
        self.left = Pin(left_pin, Pin.IN)
        self.right = Pin(right_pin, Pin.IN)

    def read(self):
        return self.left.value(), self.right.value()

# ------------------ ULTRASONIC ------------------ #
class Ultrasonic:
    def __init__(self, trig_pin, echo_pin):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def distance(self):
        self.trig.value(0); time.sleep_us(2)
        self.trig.value(1); time.sleep_us(10)
        self.trig.value(0)

        try:
            d = time_pulse_us(self.echo, 1, 30000)
            return (d * 0.0343) / 2
        except:
            return 100  # far

# ------------------ LED ------------------ #
class LED:
    def __init__(self, n):
        self.n = n

    def set(self, r, g, b):
        for i in range(1, self.n + 1):
            Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set(0, 0, 0)

# ------------------ HARDWARE SETUP ------------------ #
motor = Motor(a1_pin=Snowflake.IO3, a2_pin=Snowflake.IO4,
              b1_pin=Snowflake.IO5, b2_pin=Snowflake.IO6,
              speed=0.45, turn_speed=1.0)
  
ir = IRSensor(left_pin=Snowflake.IO17, right_pin=Snowflake.IO18)
sonic = Ultrasonic(trig_pin=Snowflake.IO15, echo_pin=Snowflake.IO16)
led = LED(9)

THRESHOLD = 18  # front wall threshold

print("Maze Solver Robot Starting...")

led.set(0, 0, 255)
time.sleep(1)
led.off()

# ------------------ MAZE LOGIC (LEFT WALL FOLLOW) ------------------ #
while True:
    dist = sonic.distance()
    L, R = ir.read()  # 1 = wall, 0 = open

    print(f"D={dist:.1f} | L={L}, R={R}")

    # If front is clear, move forward
    if dist > THRESHOLD:
        led.set(0, 255, 0)
        motor.forward()
        
    if R == 1 and L == 0:
        led.set(0, 0, 255) # Blue for right
        motor.turn_right()
        
    if R == 0 and L == 1:
        led.set(255, 150, 0) # Orange for left
        motor.turn_left()
        
    # If front is blocked by a wall
    if dist < THRESHOLD:
        motor.stop() # Stop first as requested
        time.sleep_ms(100) # Small delay to stabilize
          
        L, R = ir.read() # Re-read sensors after stopping
        print(f"Stopped. Re-checking... L={L}, R={R}")
        
        # If right is open, turn right (New Priority)
        if R == 1 and L == 0:
            led.set(0, 0, 255) # Blue for right
            motor.turn_left()
        
        elif R == 0 and L == 1:
            led.set(255, 150, 0) # Orange for left
            motor.turn_right()
            
        # Else (dead-end), make a U-turn by turning left twice
        else:
            led.set(255, 0, 0) # Red for U-turn
            motor.turn_left(600) # Turn left for a longer duration

    time.sleep_ms(50)
