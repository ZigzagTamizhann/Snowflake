from machine import Pin, PWM
import time
import Subu
# --- SETUP ---
# ESP32: Pin 15
# Pico: Pin 15
servo = PWM(Pin(Subu.IO2))
servo.freq(50)

# --- CALIBRATION VARIABLES ---
STOP_PULSE = 1500000       # 1.5ms (Value to make it stop)
FORWARD_PULSE = 2000000    # 2.0ms (Value for Max Speed)

# HOW LONG DOES ONE CIRCLE TAKE?
# You must change this number! 
# Start with 1.2 seconds. If it turns too far, lower it. If not enough, raise it.
TIME_FOR_ONE_REV = 1.2 

def stop():
    servo.duty_ns(STOP_PULSE)

def forward():
    servo.duty_ns(FORWARD_PULSE)

# --- MAIN LOOP ---
try:
    print("Loop starting...")
    stop()
    time.sleep(1)

    while True:
        print("Performing 360 rotation...")
        
        # 1. Start moving
        forward()
        

except KeyboardInterrupt:
    stop()