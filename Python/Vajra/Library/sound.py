from machine import Pin
import time
import Subu
# --- SETUP ---
# ESP32: Pin 16
# Pico: Pin 16
sensor_pin = Pin(Subu.IO3, Pin.IN)
led = Pin(2, Pin.OUT)  # Built-in LED (Pin 25 on Pico)

print("Waiting for sound...")

while True:
    # If sound is detected, the sensor sends a 1 (HIGH)
    if sensor_pin.value() == 1:
        print("sound detected")
        led.value(1) # LED ON
        time.sleep(0.1)
        led.value(0) # LED OFF
    
    # Small delay to save processor usage
    time.sleep(0.01)