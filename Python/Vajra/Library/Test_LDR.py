import time
from LDR import LDR  # Importing the class we defined in the previous file

# --- Configuration ---
LDR_PIN = 26  # GP26 is ADC0 on Raspberry Pi Pico

# --- Setup ---
# Create an instance of the LDR class
light_sensor = LDR(LDR_PIN)

print("Starting LDR Sensor readings...")
print("Press Ctrl+C to stop.")

# --- Main Loop ---
try:
    while True:
        # Get the raw value (0 - 65535)
        raw_val = light_sensor.read_raw()
        
        # Get the percentage value (0 - 100%)
        percent_val = light_sensor.read_percentage()

        # Print the values to the console
        print(f"Raw Value: {raw_val} | Light Level: {percent_val}%")
        
        # Wait for 0.5 seconds before the next read
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nProgram stopped by user.")