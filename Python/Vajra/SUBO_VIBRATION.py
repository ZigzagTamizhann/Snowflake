import Subu
from machine import Pin
import time

# --- Configuration ---
# Set the GPIO pin connected to the Vibration Sensor's 'OUT' pin
# We'll use GP6 for this example.
VIBRATION_SENSOR_PIN = 6

# Initialize the pin as an input
# Many digital vibration sensors output HIGH (1) when stable, and LOW (0) briefly when vibration/shock occurs.
# Check your sensor's documentation—you might need Pin.PULL_UP if it floats when not triggered.
vibration_sensor = Pin(VIBRATION_SENSOR_PIN, Pin.IN)

print("Vibration Sensor Monitor Started. Tap the sensor module to test.")

# --- Main Loop ---
while True:
    # Read the digital value from the sensor pin
    sensor_value = vibration_sensor.value()

    # We assume the sensor outputs LOW (0) when a shock/vibration is detected
    if sensor_value == 0:
        print("💥 Vibration/Shock Detected!")

        # Debouncing: Wait for the sensor output to return to its stable state (1)
        # This prevents the message from being spammed during a single event.
        while vibration_sensor.value() == 0:
            time.sleep(0.01)

        print("--- Sensor stabilized. ---")

    else:
        # A HIGH (1) reading means no shock/vibration is currently detected
        # print("...Awaiting shock...") # Uncomment if you want continuous status updates
        pass

    # Small delay to keep the loop from running too fast
    time.sleep(0.05)