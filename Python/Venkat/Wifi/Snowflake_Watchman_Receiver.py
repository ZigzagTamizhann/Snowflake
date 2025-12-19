import time
from machine import Pin, PWM, UART, time_pulse_us # type: ignore
import Snowflake # type: ignore
import urandom # type: ignore

# --- Hardware Abstraction Classes ---

class Ultrasonic:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
    def get_distance_cm(self):
        """Returns the distance in centimeters."""
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time_pulse_us(self.echo, 1, 30000) # 30ms timeout
            distance = (pulse_duration * 0.0343) / 2
            return distance
        except OSError:
            return -1.0

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, initial_speed=0.5):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))
        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)
        self.set_speed(initial_speed)
        self.stop()

    def set_speed(self, speed_fraction):
        speed_fraction = max(0.2, min(1.0, speed_fraction))
        self.duty_cycle = int(speed_fraction * 65535)
        self.turn_duty_cycle = int(min(1.0, speed_fraction * 1.2) * 65535)

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

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds=9):
        self.NUM_LEDS = num_leds
    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, (r, g, b))
    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware and Communication Setup ---
OBSTACLE_THRESHOLD_CM = 30

motor = Motor(
    a1_pin=Snowflake.IO3, a2_pin=Snowflake.IO4,
    b1_pin=Snowflake.IO5, b2_pin=Snowflake.IO6,
    initial_speed=0.5
)
led = LED(num_leds=9)
ultrasonic = Ultrasonic(trigger_pin=Snowflake.IO9, echo_pin=Snowflake.IO10)
uart = UART(0, baudrate=115200, tx=Snowflake.IO1, rx=Snowflake.IO2)

print("Snowflake Watchman Receiver: Patrolling...")
led.set_all(0, 0, 255)  # Blue light on startup
time.sleep(1)

# --- Main Program Loop ---
manual_override = False
last_command_time = time.ticks_ms()

while True:
    try:
        # --- Check for Manual Commands ---
        if uart.any():
            command = uart.readline().decode('utf-8').strip()
            print(f"Received command: {command}")
            manual_override = True
            last_command_time = time.ticks_ms()

            if command == 'F': motor.forward(); led.set_all(0, 255, 0)
            elif command == 'B': motor.backward(); led.set_all(255, 100, 0)
            elif command == 'L': motor.turn_left(); led.set_all(0, 0, 255)
            elif command == 'R': motor.turn_right(); led.set_all(0, 0, 255)
            elif command == 'S': motor.stop(); led.set_all(255, 0, 0)
        
        # If no manual command received for 2 seconds, return to auto mode
        if manual_override and time.ticks_diff(time.ticks_ms(), last_command_time) > 2000:
            print("Timeout, returning to automatic patrol mode.")
            manual_override = False
            motor.stop()

        # --- Automatic Patrol Mode ---
        if not manual_override:
            distance = ultrasonic.get_distance_cm()
            if distance != -1:
                uart.write(f"{distance:.1f}\n") # Send distance to sender/web

            # --- Obstacle Avoidance ---
            if 0 < distance < OBSTACLE_THRESHOLD_CM:
                print(f"Obstacle detected at {distance:.1f} cm! Avoiding.")
                led.set_all(255, 0, 0)  # Red for obstacle
                motor.stop(); time.sleep(0.2)
                motor.backward(); time.sleep(0.5)
                if urandom.choice([0, 1]) == 0: motor.turn_left()
                else: motor.turn_right()
                time.sleep(0.4)
                motor.stop()
            else:
                # --- Random Patrolling ---
                print("Patrolling...")
                led.set_all(0, 255, 0) # Green for normal operation
                move = urandom.randint(0, 2)
                if move == 0: motor.forward()
                elif move == 1: motor.turn_left()
                else: motor.turn_right()
                time.sleep(urandom.uniform(0.5, 1.5))
                motor.stop()
                time.sleep(0.5)
        else:
            # In manual mode, just send distance periodically
            distance = ultrasonic.get_distance_cm()
            if distance != -1: uart.write(f"{distance:.1f}\n")
            time.sleep_ms(100)

    except Exception as e:
        print(f"An error occurred: {e}")
        motor.stop()
        time.sleep(1)