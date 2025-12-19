import dht
from machine import Pin
import time
import Subu
# --- Configuration ---
# Change '15' to the GPIO pin number you connected the Data pin to.
SENSOR_PIN = Subu.IO2

# --- Setup ---
# Initialize the DHT11 sensor
# If you are using a DHT22, simply change dht.DHT11 to dht.DHT22
sensor = dht.DHT11(Pin(SENSOR_PIN))

print(f"Reading DHT11 Sensor on Pin {SENSOR_PIN}...")

# --- Main Loop ---
while True:
    try:
        # 1. Trigger the sensor to measure
        sensor.measure()
        
        # 2. Read the values
        temp_c = sensor.temperature() # Temperature in Celsius
        hum = sensor.humidity()       # Humidity in %
        
        # 3. Print the values
        print(f"Temperature: {temp_c}°C | Humidity: {hum}%")
        
    except OSError as e:
        # DHT sensors are sensitive and sometimes fail to read.
        # This catches errors like "ETIMEDOUT" or Checksum errors without crashing.
        print("Failed to read sensor.")
        
    # DHT11 needs at least 1-2 seconds between readings to stabilize
    time.sleep(2)
