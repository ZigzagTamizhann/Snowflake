import Subu
from machine import Pin
import time
import dht


DHT_DATA_PIN = Subu.IO3

sensor = dht.DHT11(Pin(DHT_DATA_PIN))

print("DHT11 Sensor Monitor Started.")
print("Reading temperature and humidity every 3 seconds...")
time.sleep(1)

while True:
    try:
        # 1. Measure the data
        sensor.measure()

        # 2. Get the readings
        temp_c = sensor.temperature()
        humidity = sensor.humidity()

        # 3. Print the results
        print("-" * 30)
        print(f"🌡️ Temperature: {temp_c}°C")
        print(f"💧 Humidity:    {humidity}%")

        # Optional: Convert to Fahrenheit
        temp_f = (temp_c * 9/5) + 32
        print(f"🔥 Temperature: {temp_f:.1f}°F")
        print("-" * 30)

    except OSError as e:
        # This error often occurs if the timing is off or the sensor is disconnected
        print("Failed to read sensor. Check wiring and try again.")
        # If it's a CRC error, MicroPython returns 102.
        if e.args[0] == 102:
            print("--- CRC error detected. Retrying. ---")

    time.sleep(3)