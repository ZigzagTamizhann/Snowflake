import time
from machine import Pin, PWM, time_pulse_us  # type: ignore
import Subu  # type: ignore

# -------------------------------
# MOTOR CLASS
# -------------------------------
class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, turn_speed=0.65):
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
        self.speed = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_speed = int(max(0.0, min(1.0, turn_speed)) * 65535)

    def forward(self):
        self.motor_a1.duty_u16(self.speed); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.speed); self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.speed)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.speed)

    def turn_left(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_speed)
        self.motor_b1.duty_u16(self.turn_speed); self.motor_b2.duty_u16(0)

    def turn_right(self):
        self.motor_a1.duty_u16(self.turn_speed); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_speed)

    def stop(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)


# -------------------------------
# IR CLASS
# -------------------------------
class IRSensor:
    def __init__(self, left_pin, right_pin):
        self.left = Pin(left_pin, Pin.IN)
        self.right = Pin(right_pin, Pin.IN)

    def read(self):
        # 0 = wall close, 1 = no wall
        return self.left.value(), self.right.value()


# -------------------------------
# ULTRASONIC CLASS
# -------------------------------
class Ultrasonic:
    def __init__(self, trig, echo):
        self.trig = Pin(trig, Pin.OUT)
        self.echo = Pin(echo, Pin.IN)

    def distance(self):
        self.trig.low()
        time.sleep_us(5)
        self.trig.high()
        time.sleep_us(10)
        self.trig.low()

        try:
            pulse = time_pulse_us(self.echo, 1, 30000)
            return (pulse * 0.0343) / 2
        except:
            return 999  # No reading


# -------------------------------
# LED CLASS
# -------------------------------
class LED:
    def __init__(self, num_leds):
        self.num = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.num + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)


# -------------------------------
# INITIALIZATION
# -------------------------------
motor = Motor(
    a1_pin=Subu.IO3,
    a2_pin=Subu.IO4,
    b1_pin=Subu.IO5,
    b2_pin=Subu.IO6,
    speed=0.45,
    turn_speed=0.65,
)

ir = IRSensor(left_pin=Subu.IO17, right_pin=Subu.IO18)
ultra = Ultrasonic(trig=Subu.IO15, echo=Subu.IO16)
led = LED(48)

print("Maze Solver V3 Ultra — Starting…")

time.sleep(1)
led.set_all(0, 0, 255)


# -------------------------------
# MAZE LOGIC — RIGHT HAND RULE
# -------------------------------
def maze_solver():

    while True:

        dist = ultra.distance()
        L, R = ir.read()  # 1 = free, 0 = wall

        print(f"Front={dist:.1f}  Left={L}  Right={R}")

        # PRIORITY 1 — TURN RIGHT if free
        if R == 1:
            print("Right available → Turning Right")
            led.set_all(255, 150, 0)
            motor.turn_left()
            time.sleep(0.70)
            motor.stop()
            time.sleep(2)
            continue

        # PRIORITY 2 — If front blocked → Turn Left
        if dist < 15:
            print("Front blocked → Turning Left")
            led.set_all(255, 0, 0)
            motor.turn_right()
            time.sleep(0.70)
            motor.stop()
            time.sleep(2)
            continue

        # PRIORITY 3 — Left open → Turn left
        if L == 1:
            print("Left available → Turning Left")
            led.set_all(255, 255, 0)
            motor.turn_right()
            time.sleep(0.70)
            motor.stop()
            time.sleep(2)
            
            continue

        # PRIORITY 4 — GO FORWARD
        print("Clear path → Forward")
        led.set_all(0, 255, 0)
        motor.forward()

        time.sleep(0.05)


# -------------------------------
# RUN
# -------------------------------
try:
    maze_solver()

except KeyboardInterrupt:
    motor.stop()
    led.off()
    print("Stopped by user.")


