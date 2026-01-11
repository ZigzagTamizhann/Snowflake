import time
from machine import Pin, PWM # type: ignore
import Snowflake # type: ignore
import urandom # Random selection for turning

# --- State & Constant Definitions ---
class RobotState:
    """Represents the current state of the robot's behavior."""
    FORWARD = 1
    STEER_LEFT = 2
    STEER_RIGHT = 3 # This state is no longer used by the main logic but kept for potential future use.
    AVOID_LEFT = 6  # New state for when left sensor detects
    AVOID_RIGHT = 7 # New state for when right sensor detects
    INTERSECTION_TURN = 5 # New state for intersection

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, turn_speed):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        self.motor_a1.freq(freq)
        self.motor_a2.freq(freq)
        self.motor_b1.freq(freq)
        self.motor_b2.freq(freq)

        self.set_speed(speed, turn_speed)
        self.stop()

    def set_speed(self, speed, turn_speed):
        """Sets the base forward speed and the turning speed for the motors."""
        self.duty_cycle = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_duty_cycle = int(max(0.0, min(1.0, turn_speed)) * 65535)

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle)
        self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.duty_cycle)

    def steer_left(self): # Gently steer left (towards the wall)
        self.motor_a1.duty_u16(int(self.turn_duty_cycle * 0.5))
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.turn_duty_cycle)
        self.motor_b2.duty_u16(0)

    def steer_right(self): # Gently steer right (away from the wall)
        self.motor_a1.duty_u16(self.turn_duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(int(self.turn_duty_cycle * 0.5))
        self.motor_b2.duty_u16(0)
        
    def turn_right_hard(self): # Pivot turn right to avoid obstacles
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.turn_duty_cycle)
        self.motor_b2.duty_u16(0)

    def turn_left_hard(self): # Pivot turn left
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)

    def stop(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(
    a1_pin=Snowflake.IO1, a2_pin=Snowflake.IO2,
    b1_pin=Snowflake.IO3, b2_pin=Snowflake.IO4,
    speed=0.3, turn_speed=0.5
)
left_ir_sensor = Pin(Snowflake.IO7, Pin.IN) # Left IR sensor
right_ir_sensor = Pin(Snowflake.IO15, Pin.IN) # Right IR sensor
led = LED(num_leds=9)

def startup_sequence():
    """Plays a startup animation on the LEDs."""
    print("Wall Follower Robot - Starting...")
    for i in range(1, led.NUM_LEDS + 1):
        Snowflake.setSingleLED(i, (0, 0, 255))
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

def handle_state(state):
    """Executes motor and LED actions based on the current robot state."""
    if state == RobotState.FORWARD:
        print("State: FORWARD")
        led.set_all(0, 255, 0)  # Green: Following
        motor.forward()
    elif state == RobotState.AVOID_LEFT:
        print("State: AVOID_LEFT (Left sensor detected)")
        led.set_all(255, 150, 0) # Orange
        motor.stop()
        time.sleep_ms(100)
        print("Reversing...")
        motor.backward()
        time.sleep_ms(800)
        print("Turning Right...")
        motor.turn_right_hard()
        time.sleep_ms(800) # Turn duration
        motor.stop()
        time.sleep_ms(100)
    elif state == RobotState.AVOID_RIGHT:
        print("State: AVOID_RIGHT (Right sensor detected)")
        led.set_all(0, 255, 255) # Cyan
        motor.stop()
        time.sleep_ms(100)
        print("Reversing...")
        motor.backward()
        time.sleep_ms(800)
        print("Turning Left...")
        motor.turn_left_hard()
        time.sleep_ms(800) # Turn duration
        motor.stop()
        time.sleep_ms(100)
    elif state == RobotState.INTERSECTION_TURN:
        # This handles the case where both sensors are 1
        print("State: INTERSECTION_TURN (Both sensors detected)")
        led.set_all(255, 0, 255) # Magenta for intersection
        motor.stop()
        time.sleep_ms(200)
        
        print("Reversing...")
        motor.backward()
        time.sleep_ms(1000   )
        motor.stop()
        time.sleep_ms(200)

        if urandom.choice([0, 1]) == 0:
            print("Turning Left Randomly...")
            motor.turn_left_hard()
        else:
            print("Turning Right Randomly...")
            motor.turn_right_hard()
        
        time.sleep_ms(500) # Turn duration
        motor.stop()
        time.sleep_ms(100)

# --- Main Program ---
def main():
    startup_sequence()
    while True:
        # 1. Read sensor values
        left_val = left_ir_sensor.value()
        right_val = right_ir_sensor.value()

        print(f"Sensor values: Left={left_val}, Right={right_val}")

        # 2. Determine the robot's state based on sensor inputs
        current_state = None
        if left_val == 1 and right_val == 1:
            current_state = RobotState.INTERSECTION_TURN
        elif left_val == 0 and right_val == 0:
            current_state = RobotState.FORWARD
        elif left_val == 1 and right_val == 0: # Left is 1
            current_state = RobotState.AVOID_LEFT
        else:
            current_state = RobotState.AVOID_RIGHT # Right is 1 (or L=0, R=1)

        # 3. Execute actions based on the determined state
        handle_state(current_state)

        time.sleep_ms(20)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        led.off()
        motor.stop()


