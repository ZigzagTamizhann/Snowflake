import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Subu # type: ignore
import random

# --- Hardware Abstraction Classes ---

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, Turn):
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
        self.duty_cycle = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_duty_cycle = int(max(0.0, min(1.0, Turn)) * 65535)

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
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

class Ultrasonic:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def get_distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time_pulse_us(self.echo, 1, 30000) # 30ms timeout
            return (pulse_duration * 0.0343) / 2
        except OSError:
            return -1

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds=9):
        self.NUM_LEDS = num_leds
    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1): Subu.setSingleLED(i, (r, g, b))
    def off(self): self.set_all(0, 0, 0)
# --- Main Program ---
# --- Pin Definitions ---

# --- Hardware Initialization ---

In1 = Subu.IO18
In2 = Subu.IO19
In3 = Subu.IO20
In4 = Subu.IO21

speed = 0.4
Turn = 0.4

Trig = Subu.IO1
Echo = Subu.IO4

num_leds = 48

OBSTACLE_DISTANCE_CM = 20

ultrasonic = Ultrasonic(Trig, Echo)
motor = Motor(In1, In2, In3, In4, speed, Turn)
led = LED(num_leds)


print("Obstacle Avoiding Car - Starting...")

try:
    # Startup LED sequence
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255)) # Blue
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
            motor.stop()
            time.sleep_ms(100)
            
            print("Reversing...")
            # Reversing: Set LEDs to yellow
            led.set_all(255, 150, 0) # Yellow
            motor.backward()
            time.sleep_ms(500)
            
            # Randomly choose to turn left or right
            if random.choice([0, 1]) == 0:
                print("Turning left randomly...")
                motor.turn_left()
            else:
                print("Turning right randomly...")
                motor.turn_right()

            time.sleep_ms(700)
            
            motor.stop()
            time.sleep_ms(100)
        else:
            print("Moving forward...")
            # No obstacle, moving forward: Set LEDs to green
            led.set_all(0, 255, 0) # Green
            motor.forward()

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program stopped.")
    # Cleanly stop motors and turn off LEDs
    led.off()
    motor.stop()


