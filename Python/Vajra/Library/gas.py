from machine import ADC, Pin
import time
import Subu

# 1. Setup
gas_pin = Subu.IO5
gas_sensor = ADC(Pin(gas_pin))

# 2. CALIBRATION PHASE
print("--- STARTING CALIBRATION ---")
print("Please leave the sensor in CLEAN AIR (no gas).")
print("Warming up and calibrating for 5 seconds...")

# Take 10 readings to find the average "Clean Air" value
total_value = 0
for i in range(10):
    val = gas_sensor.read_u16()
    total_value += val
    time.sleep(0.5)

# Calculate the Baseline (The normal value for your room)
baseline_value = total_value // 10

# 3. SET DYNAMIC THRESHOLDS
# We set the warning 5,000 points above your baseline
# We set the danger 15,000 points above your baseline
THRESHOLD_MILD = baseline_value + 5000
THRESHOLD_HAZARDOUS = baseline_value + 15000

print(f"Calibration Complete!")
print(f"Baseline (Clean Air): {baseline_value}")
print(f"Mild Warning set at:  {THRESHOLD_MILD}")
print(f"Hazard Danger set at: {THRESHOLD_HAZARDOUS}")
print("--------------------------------")
time.sleep(2)

# 4. MONITORING LOOP
while True:
    reading = gas_sensor.read_u16()
    
    status = ""
    if reading < THRESHOLD_MILD:
        status = "Ambient (Clean)"
    elif reading >= THRESHOLD_MILD and reading < THRESHOLD_HAZARDOUS:
        status = "WARNING: Mild Gas Detected"
    else:
        status = "DANGER: Hazardous Gas Detected!"
    
    print(f"Value: {reading} (Base: {baseline_value}) | Status: {status}")
    
    time.sleep(1)