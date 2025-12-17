from machine import Pin
import time
import Subu

# 1. Setup the Relay Pin
# We use Pin.OUT because we are sending a signal OUT to the relay
relay_pin = Pin(Subu.IO2, Pin.OUT)

print("Relay Test Starting...")

while True:
    # -------------------------------------------------
    # TURN ON
    # -------------------------------------------------
    print("Relay ON (Click!)")
    
    # Try 1 first. If your relay stays OFF, change this to 0.
    relay_pin.value(1)  
    
    time.sleep(2)

    # -------------------------------------------------
    # TURN OFF
    # -------------------------------------------------
    print("Relay OFF")
    
    # Try 0 first. If your relay stays ON, change this to 1.
    relay_pin.value(0)
    
    time.sleep(2)