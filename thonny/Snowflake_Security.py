import time
from machine import Pin, PWM, UART # type: ignore
import Snowflake # type: ignore 
import random

# --- Configuration Constants ---
FORWARD_SPEED = 0.3 # Reduced speed as requested
TURN_SPEED = 0.6

# Sensor Thresholds
OBSTACLE_DISTANCE_CM = 25.0 # How close an object must be to be an "obstacle"
ULTRASONIC_TIMEOUT_US = 50000 # Timeout for sensor readings

# --- Grid and Orientation Constants ---
GRID_ROWS = 3
GRID_COLS = 3

# Robot orientation constants
NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

# --- Hardware Abstraction Classes ---

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))
        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)
        self.stop()

    def set_speed(self, forward_speed, turn_speed):
        self.forward_duty = int(forward_speed * 65535)
        self.turn_duty = int(turn_speed * 65535)

    def forward(self):
        self.motor_a1.duty_u16(self.forward_duty); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.forward_duty); self.motor_b2.duty_u16(0)

    def turn_left(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty)
        self.motor_b1.duty_u16(self.turn_duty); self.motor_b2.duty_u16(0)

    def turn_right(self):
        self.motor_a1.duty_u16(self.turn_duty); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty)

    def stop(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)

class UltrasonicSensor:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trig_pin, echo_pin):
        self.trigger = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def get_distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = time.ticks_us()
            while self.echo.value() == 0:
                if time.ticks_diff(time.ticks_us(), pulse_time) > ULTRASONIC_TIMEOUT_US: return -1
            pulse_start = time.ticks_us()
            while self.echo.value() == 1:
                if time.ticks_diff(time.ticks_us(), pulse_start) > ULTRASONIC_TIMEOUT_US: return -1
            pulse_end = time.ticks_us()
            distance = (time.ticks_diff(pulse_end, pulse_start) * 0.0343) / 2
            return distance
        except OSError:
            return -1

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1): Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(Snowflake.IO17, Snowflake.IO18, Snowflake.IO19, Snowflake.IO20)
motor.set_speed(FORWARD_SPEED, TURN_SPEED)

sensor = UltrasonicSensor(trig_pin=Snowflake.IO11, echo_pin=Snowflake.IO12)
led = LED(num_leds=9)

# --- UART Communication for Web Display ---
# Use UART(0) for communication over the USB cable
uart = UART(0, 115200)

# --- High-Level Robot Actions ---

def move_forward(duration):
    # This function is no longer used with the non-blocking approach
    pass

def scan_for_obstacle():
    """
    Checks for an obstacle and returns the distance.
    It sends the distance and status via UART.
    """
    distance = sensor.get_distance_cm()

    if distance > 0:
        msg = f"Distance measured: {distance:.1f} cm\n"
        print(msg.strip())
        uart.write(msg)
    else:
        uart.write("Distance measured: -1.0\n")

    if 0 < distance < OBSTACLE_DISTANCE_CM:
        print("!!! OBSTACLE DETECTED !!!")
        uart.write("STATUS:!!! OBSTACLE DETECTED !!!\n")
        led.set_all(255, 0, 0) # Red
        return True # Obstacle detected
    else:
        return False # No obstacle

# --- Main Surveillance Routine ---

def start_patrol():
    """Main function to perform a continuous surveillance patrol."""
    print("--- Starting 3x3 Grid Security Patrol ---")
    TURN_90_DURATION = 0.55  # Calibrated time for a 90-degree turn
    MOVE_CELL_DURATION = 1.5 # Time to move one cell

    # --- Robot State ---
    robot_row = 0
    robot_col = 0
    robot_orientation = EAST  # தொடக்கத்தில் கிழக்கு திசையை நோக்கி இருக்கும்
    
    # ரோபோவின் நிலையை கண்காணிக்க புதிய மாறிகள்
    # 'IDLE', 'MOVING', 'TURNING_R', 'TURNING_L'
    robot_action = 'IDLE'
    action_start_time = 0
    action_duration = 0

    while True:
        # Always scan for obstacles and send data
        obstacle_found = scan_for_obstacle()

        # If an obstacle is found while moving, stop and react
        if obstacle_found and robot_action == 'MOVING':
            motor.stop()
            robot_action = 'IDLE'
            print("Obstacle detected while moving! Stopping and turning.")
            time.sleep(0.5) # Pause
            
            # Start a non-blocking turn
            print("Starting a non-blocking turn right.")
            motor.turn_right()
            robot_action = 'TURNING_R'
            action_start_time = time.ticks_ms()
            action_duration = TURN_90_DURATION * 1000
            robot_orientation = (robot_orientation + 1) % 4
            continue

        # --- Action Handler: Check if current action is complete ---
        if robot_action != 'IDLE':
            if time.ticks_diff(time.ticks_ms(), action_start_time) > action_duration:
                motor.stop()
                print(f"Action '{robot_action}' complete.")
                
                # Update position only if it was a move action
                if robot_action == 'MOVING':
                    if robot_orientation == NORTH: robot_row -= 1
                    elif robot_orientation == EAST: robot_col += 1
                    elif robot_orientation == SOUTH: robot_row += 1
                    elif robot_orientation == WEST: robot_col -= 1
                    robot_row = max(0, min(robot_row, GRID_ROWS - 1))
                    robot_col = max(0, min(robot_col, GRID_COLS - 1))
                
                robot_action = 'IDLE' # Ready for a new decision

        # --- Decision Maker: Only make a new decision if the robot is idle ---
        if robot_action == 'IDLE':
            pos_msg = f"Position: ({robot_row}, {robot_col}), Facing: {['N','E','S','W'][robot_orientation]}\n"
            print(f"\n{pos_msg.strip()}")
            uart.write(pos_msg)
            uart.write("STATUS:Deciding next move...\n")
            led.set_all(0, 0, 255) # Blue while deciding
            time.sleep(0.5) # Pause to show decision state

            # Check for grid boundaries
            boundary_ahead = False
            if robot_orientation == NORTH and robot_row == 0: boundary_ahead = True
            elif robot_orientation == EAST and robot_col == GRID_COLS - 1: boundary_ahead = True
            elif robot_orientation == SOUTH and robot_row == GRID_ROWS - 1: boundary_ahead = True
            elif robot_orientation == WEST and robot_col == 0: boundary_ahead = True # type: ignore

            if boundary_ahead:
                print("Boundary detected. Turning right.")
                uart.write("STATUS:Boundary Detected\n")
                motor.turn_right()
                robot_action = 'TURNING_R'
                action_start_time = time.ticks_ms()
                action_duration = TURN_90_DURATION * 1000
                robot_orientation = (robot_orientation + 1) % 4
            else:
                # Path is clear, start moving forward
                print("Path clear. Moving forward one cell.")
                uart.write("STATUS:Path is Clear\n")
                led.set_all(0, 255, 0) # Green for moving
                motor.forward()
                robot_action = 'MOVING'
                action_start_time = time.ticks_ms()
                action_duration = MOVE_CELL_DURATION * 1000

        time.sleep_ms(50) # Loop delay to prevent high CPU usage

if __name__ == "__main__":
    try:
        start_patrol()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        motor.stop()
        led.off()
        print("Robot has stopped.")