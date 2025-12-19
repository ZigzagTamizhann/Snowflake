import time
from vibration_sensor import VibrationSensor # type: ignore
import Subu # type: ignore
# --- Configuration ---
VIB_PIN = Subu.IO2

# --- The Interrupt Handler ---
# This function runs AUTOMATICALLY when vibration happens.
def detected_vibration(pin):
    print("(!) INTERRUPT: VIBRATION DETECTED!")

# --- Setup ---
vib_sensor = VibrationSensor(VIB_PIN)

# Tell the sensor: "When you feel shaking, run the 'detected_vibration' function"
vib_sensor.set_callback(detected_vibration)

print("System Arming...")
time.sleep(1)
print("System Ready. Shake the sensor!")

# --- Main Loop ---
# The loop can now do other things (like blink an LED) or just wait.
# The sensor will work even if this loop is 'sleeping'.
try:
    while True:
        print("Scanning for activity...")
        time.sleep(2) # Long sleep to prove the interrupt works instantly

except KeyboardInterrupt:
    print("\nStopped.")