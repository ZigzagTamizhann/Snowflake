import Subu
from machine import Pin
import time

# --- Configuration ---
# Define the GPIO pins connected to the sensor
TRIG_PIN = Subu.IO1
ECHO_PIN = Subu.IO2

# Initialize the pins
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# Speed of Sound (constants for calculation)
# 1. For Centimeters: 34300 cm/s -> 0.01715 cm/us (divided by 2 for round trip)
CM_FACTOR = 0.01715
# 2. For Inches: 13500 inches/s -> 0.00669 inches/us (divided by 2 for round trip)
INCH_FACTOR = 0.00669

# Maximum duration to wait for echo pulse (500ms for safety)
MAX_TIMEOUT_US = 500000

print("Ultrasonic Sensor Monitor Started. Measuring distance...")

# --- Distance Measurement Function ---
def get_distance_cm():
    """Measures the distance in centimeters using the HC-SR04."""
    
    # Reset trigger pin to LOW
    trig.value(0)
    time.sleep_us(2)

    # 1. Send 10 microsecond pulse to trigger sensor
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # 2. Measure the duration of the echo pulse
    
    # Wait for the Echo pin to go HIGH (pulse start)
    pulse_start = time.ticks_us()
    timeout_start = pulse_start
    while echo.value() == 0:
        pulse_start = time.ticks_us()
        if time.ticks_diff(pulse_start, timeout_start) > MAX_TIMEOUT_US:
            return -1 # Timeout error

    # Wait for the Echo pin to go LOW (pulse end)
    pulse_end = pulse_start
    timeout_start = time.ticks_us()
    while echo.value() == 1:
        pulse_end = time.ticks_us()
        if time.ticks_diff(pulse_end, timeout_start) > MAX_TIMEOUT_US:
            return -1 # Timeout error
            
    # Calculate pulse duration
    pulse_duration = time.ticks_diff(pulse_end, pulse_start)

    # Calculate distance in centimeters
    distance_cm = pulse_duration * CM_FACTOR
    
    return distance_cm

# --- Utility Function for Inches ---
def cm_to_inches(cm):
    """Converts distance from cm to inches."""
    return cm / 2.54

# --- Main Loop ---
while True:
    distance_cm = get_distance_cm()

    if distance_cm > 0:
        distance_inch = cm_to_inches(distance_cm)
        
        print("-" * 35)
        print(f"📏 Distance (CM): {distance_cm:.2f} cm")
        print(f"📐 Distance (IN): {distance_inch:.2f} in")
        print("-" * 35)
        
    else:
        print("❌ Measurement Error/Timeout: Check Sensor Connection.")

    # Read sensor every 0.2 seconds for fast updates
    time.sleep(0.2)