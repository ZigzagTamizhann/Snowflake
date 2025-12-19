import Subu # type: ignore
from machine import Pin # type: ignore
import time

# --- Configuration ---
# Set the GPIO pin connected to the Touch Sensor's 'OUT' pin
# We'll use GP2 for this example.
TOUCH_SENSOR_PIN = Subu.IO3

# Initialize the pin as an input
# We use Pin.PULL_UP to ensure the pin is held high when the sensor is NOT touched,
# preventing 'floating' readings.
touch_sensor = Pin(TOUCH_SENSOR_PIN, Pin.IN, Pin.PULL_UP)

print("Touch Sensor Monitor Started. Touch the sensor pad to test.")

# --- Main Loop ---
while True:
    # Read the digital value from the touch sensor pin
    # The common TTP223 module outputs LOW when touched.
    sensor_value = touch_sensor.value()

    if sensor_value == 0:
        # A LOW (0) reading means the sensor is active/touched
        print("👆 Sensor Touched!")

        # Debouncing: Wait until the touch is released before checking again
        # This prevents the message from flooding the console while held down.
        while touch_sensor.value() == 0:
            time.sleep(0.01)

    else:
        # A HIGH (1) reading means the sensor is released/not touched
        print("➖ Waiting for Touch...")

    # Small delay to keep the loop from running too fast
    time.sleep(0.1)