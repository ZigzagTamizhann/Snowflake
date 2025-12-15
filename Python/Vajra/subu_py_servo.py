import Subu
from machine import Pin, PWM
import time

# --- Configuration ---
# Set the GPIO pin connected to the servo's Signal (Yellow/Orange) wire
# GP0 is used here as an example, but you can use any PWM-capable pin
SERVO_PIN = Subu.IO4

# --- Setup PWM ---
# Initialize PWM on the specified pin
servo_pwm = PWM(Pin(SERVO_PIN))

# Set the standard frequency for hobby servos (50 Hz)
servo_pwm.freq(50)

# --- Functions for Servo Control ---

def set_angle(angle):
    """
    Calculates the duty cycle needed for a given angle (0-180 degrees)
    and sets the servo position.

    Typical servo duty cycle range for 50Hz:
    0 degrees (minimum pulse width of 0.5ms): Duty Cycle around 1500
    90 degrees (center pulse width of 1.5ms): Duty Cycle around 4500
    180 degrees (maximum pulse width of 2.5ms): Duty Cycle around 7500

    Duty cycle is a value from 0 to 65535 (16-bit resolution).
    The formula below maps 0-180 degrees to the required duty cycle range.
    """
    # Map the angle (0-180) to the duty cycle range (1500 to 7500)
    # The constants (6000 and 1500) are specific to the 50Hz frequency (65535 max duty)
    min_duty = 1500
    max_duty = 7500
    duty = int(min_duty + (max_duty - min_duty) * (angle / 180))

    # Set the PWM duty cycle
    servo_pwm.duty_u16(duty)
    print(f"Set angle: {angle}° (Duty: {duty})")


# --- Main Demonstration Loop ---

print("Servo Motor Control Started. Press Ctrl+C to stop.")
time.sleep(1) # Wait for servo to initialize

# Move the servo through a sequence of angles
try:
    while True:
        # Move to 0 degrees
        set_angle(0)
        time.sleep(1)

        # Move to 90 degrees (center)
        set_angle(90)
        time.sleep(1)

        # Move to 180 degrees
        set_angle(180)
        time.sleep(1)

        # Move back to 45 degrees
        set_angle(45)
        time.sleep(1)

except KeyboardInterrupt:
    # Cleanup when the script is stopped
    servo_pwm.deinit()
    print("\nServo motor stopped and PWM deinitialized.")