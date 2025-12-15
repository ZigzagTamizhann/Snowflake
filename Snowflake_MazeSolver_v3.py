import time
from machine import Pin, PWM # type: ignore
import Snowflake # type: ignore

# --- Configuration Constants ---

# Maze Dimensions
MAZE_ROWS = 6
MAZE_COLS = 8

# Speeds (0.0 to 1.0)
FORWARD_SPEED = 0.2
TURN_SPEED = 0.55

# Durations (in milliseconds) - IMPORTANT: These require calibration for your specific robot!
MOVE_FORWARD_DURATION_MS = 1000 # Time to move forward one 20cm cell
TURN_90_DURATION_MS = 450     # Time for a 90-degree pivot turn

# Sensor Thresholds
WALL_AHEAD_DISTANCE_CM = 15.0 # Ultrasonic threshold for a wall in front

# Timeouts
ULTRASONIC_TIMEOUT_US = 50000 # Timeout for ultrasonic sensor readings

# --- Robot Orientation ---
NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

# --- Maze Cell States ---
UNVISITED, VISITED, DEAD_END, EXIT = 0, 1, 2, 3

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

    def set_speed(self, forward_duty, turn_duty):
        self.forward_duty = forward_duty
        self.turn_duty = turn_duty

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

class IRSensors:
    """Reads state from left and right IR sensors."""
    def __init__(self, left_pin, right_pin):
        self.left = Pin(left_pin, Pin.IN)
        self.right = Pin(right_pin, Pin.IN)

    def read_values(self):
        # Assuming 0 = wall detected, 1 = no wall
        return (self.left.value() == 0, self.right.value() == 0)

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1): Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(Snowflake.IO1, Snowflake.IO2, Snowflake.IO3, Snowflake.IO4)
motor.set_speed(int(FORWARD_SPEED * 65535), int(TURN_SPEED * 65535))

front_ultrasonic = UltrasonicSensor(trig_pin=Snowflake.IO9, echo_pin=Snowflake.IO11)
ir_sensors = IRSensors(left_pin=Snowflake.IO5, right_pin=Snowflake.IO6)
led = LED(num_leds=9)

# --- Maze State Variables ---
robot_pos = {'row': 0, 'col': 0}
robot_orientation = NORTH

maze_grid = [[UNVISITED for _ in range(MAZE_COLS)] for _ in range(MAZE_ROWS)]
EXIT_POS = {'row': MAZE_ROWS - 1, 'col': MAZE_COLS - 1}
maze_grid[robot_pos['row']][robot_pos['col']] = VISITED
maze_grid[EXIT_POS['row']][EXIT_POS['col']] = EXIT

path_stack = []

# --- High-Level Robot Actions ---

def move_one_cell():
    """Moves the robot forward one cell and updates its internal position."""
    motor.forward()
    led.set_all(0, 255, 0) # Green
    time.sleep_ms(MOVE_FORWARD_DURATION_MS)
    motor.stop()
    time.sleep_ms(100) # Pause for stability

    if robot_orientation == NORTH: robot_pos['row'] -= 1
    elif robot_orientation == EAST: robot_pos['col'] += 1
    elif robot_orientation == SOUTH: robot_pos['row'] += 1
    elif robot_orientation == WEST: robot_pos['col'] -= 1

def turn_robot_left():
    """Turns the robot 90 degrees left and updates its orientation."""
    global robot_orientation
    motor.turn_left()
    led.set_all(0, 0, 255) # Blue
    time.sleep_ms(TURN_90_DURATION_MS)
    motor.stop()
    time.sleep_ms(100) # Pause for stability
    robot_orientation = (robot_orientation - 1 + 4) % 4

def turn_robot_right():
    """Turns the robot 90 degrees right and updates its orientation."""
    global robot_orientation
    motor.turn_right()
    led.set_all(255, 150, 0) # Orange
    time.sleep_ms(TURN_90_DURATION_MS)
    motor.stop()
    time.sleep_ms(100) # Pause for stability
    robot_orientation = (robot_orientation + 1) % 4

def turn_robot_180():
    """Turns the robot 180 degrees and updates its orientation."""
    global robot_orientation
    motor.turn_right()
    led.set_all(255, 0, 0) # Red
    time.sleep_ms(TURN_90_DURATION_MS * 2)
    motor.stop()
    time.sleep_ms(100) # Pause for stability
    robot_orientation = (robot_orientation + 2) % 4

# --- Maze Logic Helper Functions ---

def get_coords_in_direction(direction):
    """Calculates coordinates of the cell in the given absolute direction."""
    r, c = robot_pos['row'], robot_pos['col']
    if direction == NORTH: r -= 1
    elif direction == EAST: c += 1
    elif direction == SOUTH: r += 1
    elif direction == WEST: c -= 1
    return r, c

def is_valid_and_unexplored(row, col):
    """Checks if a cell is within bounds and is not a dead end or already visited."""
    if not (0 <= row < MAZE_ROWS and 0 <= col < MAZE_COLS):
        return False
    return maze_grid[row][col] in [UNVISITED, EXIT]

def sense_walls():
    """Returns a dictionary of booleans indicating physical wall presence."""
    front_dist = front_ultrasonic.get_distance_cm()
    wall_left, wall_right = ir_sensors.read_values()
    return {
        'front': (0 < front_dist < WALL_AHEAD_DISTANCE_CM),
        'left': wall_left,
        'right': wall_right
    }

# --- Main Program ---

def main():
    print("Advanced Maze Solver v3 - Starting...")
    led.set_all(255, 0, 255); time.sleep_ms(1000); led.off()

    while robot_pos != EXIT_POS:
        print(f"At ({robot_pos['row']},{robot_pos['col']}) facing {robot_orientation}. Path stack size: {len(path_stack)}")
        maze_grid[robot_pos['row']][robot_pos['col']] = VISITED

        # 1. Sense physical walls
        walls = sense_walls()

        # 2. Check for available paths (not physically blocked AND not a dead end/visited)
        # Get absolute directions relative to robot's orientation
        dir_left = (robot_orientation - 1 + 4) % 4
        dir_front = robot_orientation
        dir_right = (robot_orientation + 1) % 4

        # Get coordinates for each potential path
        left_coords = get_coords_in_direction(dir_left)
        front_coords = get_coords_in_direction(dir_front)
        right_coords = get_coords_in_direction(dir_right)

        # Check if paths are viable (no wall AND leads to an explorable cell)
        can_go_left = not walls['left'] and is_valid_and_unexplored(*left_coords)
        can_go_front = not walls['front'] and is_valid_and_unexplored(*front_coords)
        can_go_right = not walls['right'] and is_valid_and_unexplored(*right_coords)

        # 3. Decision Logic (Prioritized: Left -> Front -> Right -> Backtrack)
        if can_go_left:
            print("Decision: Path open on Left. Turning left.")
            path_stack.append(robot_pos.copy()) # Save current position for backtracking
            turn_robot_left()
            move_one_cell()
        elif can_go_front:
            print("Decision: Path open in Front. Moving forward.")
            path_stack.append(robot_pos.copy())
            move_one_cell()
        elif can_go_right:
            print("Decision: Path open on Right. Turning right.")
            path_stack.append(robot_pos.copy())
            turn_robot_right()
            move_one_cell()
        else:
            # Dead End: No viable paths forward, must backtrack.
            print("Decision: Dead end reached. Backtracking...")
            maze_grid[robot_pos['row']][robot_pos['col']] = DEAD_END

            if not path_stack:
                print("FATAL ERROR: Maze is unsolvable or robot is trapped!")
                led.set_all(255, 0, 0)
                motor.stop()
                while True: time.sleep_ms(1000) # Halt program

            # Pop the previous cell's coordinates from the stack
            previous_pos = path_stack.pop()

            # Figure out which direction leads back to the previous cell
            # This is a robust way to re-orient the robot correctly.
            if previous_pos['row'] < robot_pos['row']: target_orientation = NORTH
            elif previous_pos['row'] > robot_pos['row']: target_orientation = SOUTH
            elif previous_pos['col'] < robot_pos['col']: target_orientation = WEST
            else: target_orientation = EAST

            # Turn to face the previous cell
            while robot_orientation != target_orientation:
                turn_robot_right() # Turn right until facing the correct way

            # Move back to the previous cell
            print(f"Moving back to ({previous_pos['row']},{previous_pos['col']})")
            move_one_cell()

        time.sleep_ms(50) # Brief pause between decision cycles

    # Maze Solved!
    print(f"SUCCESS: Reached exit at ({robot_pos['row']},{robot_pos['col']})")
    led.set_all(0, 255, 255) # Cyan for success
    motor.stop()
    while True: time.sleep_ms(1000)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        motor.stop()
        led.off()
    except Exception as e:
        print(f"An error occurred: {e}")
        motor.stop()
        led.off()