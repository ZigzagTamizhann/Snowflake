import Subu # type: ignore
from machine import Pin # type: ignore
import time

# --- Configuration ---
# Set the GPIO pin connected to the PIR Sensor's 'OUT' pin
# We'll use GP3 for this example.
PIR_SENSOR_PIN = Subu.IO3

# Initialize the pin as an input
# The PIR sensor provides its own HIGH/LOW signal, so no internal pull-up/down is needed.
pir_sensor = Pin(PIR_SENSOR_PIN, Pin.IN)

print("PIR Motion Sensor Monitor Started. Wait for calibration...")

# --- Calibration Delay ---
# PIR sensors typically need 30-60 seconds to calibrate upon startup.
# They will often output HIGH during this time.
time.sleep(10) # Using a shorter delay for testing purposes
print("Calibration complete. Monitoring for motion...")

# --- Main Loop ---
while True:
    # Read the digital value from the PIR sensor pin
    sensor_value = pir_sensor.value()

    # The PIR sensor outputs HIGH (1) when motion is detected
    if sensor_value == 1:
        print("🚨 Motion Detected!")

        # Wait while motion is still detected (the duration is set by the sensor's own timer)
        while pir_sensor.value() == 1:
            time.sleep(0.1)

        # Print a message once the sensor resets to LOW
        print("--- Motion Ended ---")

    # If the sensor value is 0, no motion is currently detected
    else:
      
        pass

    # A short delay to prevent the loop from consuming too much processing power
    time.sleep(0.1)