import time
from pir_sensor import PIR  # Importing the class we defined above
import Subu
# --- Configuration ---
PIR_PIN = Subu.IO2 # GPIO Pin connected to the sensor output

# --- Setup ---
motion_sensor = PIR(PIR_PIN)

print("Initializing PIR Sensor...")
print("Please wait for the sensor to stabilize (warm-up)...")
time.sleep(2)  # Most PIR sensors need a moment to settle after power-up
print("Ready! Detecting motion...")

# --- Main Loop ---
try:
    while True:
        # Check the sensor status using our class method
        if motion_sensor.is_active():
            print("(!) Motion Detected!")
            
            # Optional: Add a small delay so we don't spam the print statement
            # while the sensor pin is still high.
            time.sleep(0.5) 
            
        else:
            # Uncomment the line below if you want to see "No Motion" constantly
            # print("No Motion...") 
            pass

        # Small delay to keep the loop running smoothly
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nProgram stopped by user.")