import Subu 
from machine import Pin
import time

IR_SENSOR_PIN = Subu.IO3

ir_sensor = Pin(IR_SENSOR_PIN, Pin.IN)

print("IR Sensor Monitor Started. Press Ctrl+C to stop.")

# --- Main Loop ---
while True:
    # Read the digital value from the IR sensor pin
    sensor_value = ir_sensor.value()

    # The logic might be inverted depending on the specific sensor module:
    # If ir_sensor.value() is 0, an object is DETECTED.
    if sensor_value == 0:
        print("🚨 Object Detected!")

    else:
        print("✅ No Object")

    # Wait for a short time before checking again
    time.sleep(0.2)