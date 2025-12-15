import Subu
from machine import Pin
import time

# --- Configuration ---
# Set the GPIO pin connected to the Sound Sensor's Digital Output (D0) pin
# We'll use GP10 for this example.
SOUND_SENSOR_PIN = 10

# Initialize the pin as an input
# We assume the sensor output is LOW (0) when a loud sound is detected.
sound_sensor = Pin(SOUND_SENSOR_PIN, Pin.IN)

print("Sound Sensor Monitor Started.")
print("Adjust the sensor's potentiometer to set the detection threshold.")
time.sleep(1)

# --- Main Loop ---
while True:
    # Read the digital value from the sound sensor pin
    sensor_value = sound_sensor.value()

    # The logic depends on your sensor, but often D0 goes LOW upon detection:
    if sensor_value == 0:
        print("🔊 Loud Sound Detected!")

        # Debouncing: Wait for the sound level to drop below the threshold
        # This prevents the message from repeating rapidly during a single noise event.
        while sound_sensor.value() == 0:
            time.sleep(0.01)

        print("--- Sound ended. ---")

    # If the sensor value is 1, no loud sound is currently detected
    else:
        # print("...Listening...") # Uncomment if you want continuous status updates
        pass

    # Small delay to prevent the loop from running too fast
    time.sleep(0.05)