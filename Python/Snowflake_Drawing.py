import time
from machine import Pin, PWM # type: ignore
import Snowflake # type: ignore

# --- Motor Class Definition ---
# This class controls the robot's motors.
class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed):
        """Initializes the motor driver pins using PWM for speed control."""
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        self.motor_a1.freq(freq)
        self.motor_a2.freq(freq)
        self.motor_b1.freq(freq)
        self.motor_b2.freq(freq)

        self.set_speed(speed)
        self.stop()

    def set_speed(self, speed):
        """Sets motor speed. speed is a value between 0.0 and 1.0."""
        speed = max(0.0, min(1.0, speed)) # Clamp speed between 0 and 1
        self.duty_cycle = int(speed * 65535)
        self.turn_duty_cycle = int(0.8 * 65535) # Separate, higher speed for turning

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

    def turn_left(self):
        self.motor_a1.duty_u16(self.turn_duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.turn_duty_cycle)

    def turn_right(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle)
        self.motor_b2.duty_u16(0)

    def stop(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)

# --- Shape Drawing Functions ---

def draw_square(motor, side_duration, turn_duration):
    """
    Makes the robot draw a square.
    - side_duration: How many seconds to move forward for each side.
    - turn_duration: How many seconds to turn for each corner.
    """
   
    print("Drawing a square...")
    for _ in range(4):
        print("Moving forward...")
        motor.forward()
        time.sleep(side_duration)
        
        print("Turning right...")
        motor.turn_right()
        time.sleep(turn_duration)
    
    motor.stop()
    print("Square complete!")

def draw_circle(motor, duration):
    """
    Makes the robot attempt to draw a circle by turning one motor on.
    - duration: How long the robot should execute the circle maneuver.
    """
    print("Drawing a circle...")
    # To make a circle, we can activate one side's motors to pivot.
    # This is a simplified approach.
    motor.motor_a1.duty_u16(motor.turn_duty_cycle)
    motor.motor_a2.duty_u16(0)
    motor.motor_b1.duty_u16(int(motor.turn_duty_cycle * 0.2)) # Inner wheel moves slower
    motor.motor_b2.duty_u16(0)
    
    time.sleep(duration)
    motor.stop()
    print("Circle complete!")

def draw_triangle(motor, side_duration, turn_duration):
    """
    Makes the robot draw an equilateral triangle.
    - side_duration: How many seconds to move forward for each side.
    - turn_duration: How many seconds to turn for each 120-degree corner.
    """
    print("Drawing a triangle...")
    for _ in range(3):
        print("Moving forward...")
        motor.forward()
        time.sleep(side_duration)
        
        print("Turning right (120 degrees)...")
        motor.turn_right()
        time.sleep(turn_duration) # A 120-degree turn needs more time than 90
    
    motor.stop()
    print("Triangle complete!")

def draw_rectangle(motor, length_duration, width_duration, turn_duration):
    """
    Makes the robot draw a rectangle.
    - length_duration: How many seconds to move for the long sides.
    - width_duration: How many seconds to move for the short sides.
    - turn_duration: How many seconds for a 90-degree turn.
    """
    print("Drawing a rectangle...")
    for i in range(2):
        print("Moving forward (length)...")
        motor.forward()
        time.sleep(length_duration)
        
        print("Turning right...")
        motor.turn_right()
        time.sleep(turn_duration)

        print("Moving forward (width)...")
        motor.forward()
        time.sleep(width_duration)

        print("Turning right...")
        motor.turn_right()
        time.sleep(turn_duration)
    
    motor.stop()
    print("Rectangle complete!")

def draw_pentagon(motor, side_duration, turn_duration):
    """
    Makes the robot draw a regular pentagon.
    A 72-degree turn is needed (360 / 5).
    """
    print("Drawing a pentagon...")
    for _ in range(5):
        motor.forward()
        time.sleep(side_duration)
        motor.turn_right()
        time.sleep(turn_duration) # Calibrated for a 72-degree turn
    motor.stop()
    print("Pentagon complete!")

def draw_hexagon(motor, side_duration, turn_duration):
    """
    Makes the robot draw a regular hexagon.
    A 60-degree turn is needed (360 / 6).
    """
    print("Drawing a hexagon...")
    for _ in range(6):
        motor.forward()
        time.sleep(side_duration)
        motor.turn_right()
        time.sleep(turn_duration) # Calibrated for a 60-degree turn
    motor.stop()
    print("Hexagon complete!")

# --- Main Program ---
if __name__ == "__main__":
    # Initialize the motor with your specific pins and a default speed
    motor = Motor(a1_pin=Snowflake.IO17, a2_pin=Snowflake.IO18, b1_pin=Snowflake.IO19, b2_pin=Snowflake.IO20, speed=0.4)

    # --- IMPORTANT CALIBRATION STEP ---
    # You need to find the right 'turn_duration' for a 90-degree turn.
    # Uncomment the following lines to test and find the right value.
    # print("Calibration: Testing a 0.5 second turn. Adjust as needed.")
    # motor.turn_right()
    # time.sleep(0.5) # Change this value (e.g., 0.4, 0.6) until it's a 90-degree turn
    # motor.stop()
    # time.sleep(3) # Pause to observe

    try:
        # The robot will now draw all six shapes in sequence.
        
        # --- 1. Square ---
        print("\n--- Starting Shape 1: Square ---")
        # You must calibrate the turn_duration for a 90-degree turn first!
        # Using your calibrated value of 0.55s.
        draw_square(motor, side_duration=2, turn_duration=0.55)
        print("\nTaking a 5-second break..."); time.sleep(5)

        # --- 2. Circle ---
        print("\n--- Starting Shape 2: Circle ---")
        draw_circle(motor, duration=4)
        print("\nTaking a 5-second break..."); time.sleep(5)

        # --- 3. Rectangle ---
        print("\n--- Starting Shape 3: Rectangle ---")
        draw_rectangle(motor, length_duration=3, width_duration=1.5, turn_duration=0.55)
        print("\nTaking a 5-second break..."); time.sleep(5)

        # --- 4. Triangle ---
        print("\n--- Starting Shape 4: Triangle ---")
        # A 120-degree turn needs a longer duration: 0.55 * (120/90) = 0.73s
        draw_triangle(motor, side_duration=2, turn_duration=0.73)
        print("\nTaking a 5-second break..."); time.sleep(5)

        # --- 5. Pentagon ---
        print("\n--- Starting Shape 5: Pentagon ---")
        # A 72-degree turn needs a shorter duration: 0.55 * (72/90) = 0.44s
        draw_pentagon(motor, side_duration=2, turn_duration=0.44)
        print("\nTaking a 5-second break..."); time.sleep(5)

        # --- 6. Hexagon ---
        print("\n--- Starting Shape 6: Hexagon ---")
        # A 60-degree turn needs a shorter duration: 0.55 * (60/90) = 0.37s
        draw_hexagon(motor, side_duration=1.5, turn_duration=0.37)

        print("\n\n*** Shape drawing routine complete! ***")

    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        # Cleanly stop motors
        motor.stop()
        print("Robot has stopped.")
