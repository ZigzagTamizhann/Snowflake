from machine import Pin # type: ignore
import time
import Subu # type: ignore  # type: ignore # Assuming you are using the Subu library

# Setup the sensor pin
# Replace Subu.IO1 with the actual pin you connected the SIG wire to
touch_sensor = Pin(Subu.IO2, Pin.IN) 

print("Touch sensor ready...")

while True:
    if touch_sensor.value() == 1:
        print("Touched!")
    else:
        print("Not touched") # Uncomment to see constant status
        pass
        
    time.sleep(0.5)  # Small delay to prevent spamming