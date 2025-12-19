from machine import Pin, PWM # type: ignore
import time
import Subu # type: ignore # type: ignore
# --- CONFIGURATION ---
# Define the two pins connecting to the Driver (IN1, IN2)
# ESP32: 14, 15
# Pico: 14, 15
IN1_PIN = Subu.IO3
IN2_PIN = Subu.IO4

# Setup PWM on both pins (Frequency 1000Hz is standard for motors)
motor_p1 = PWM(Pin(IN1_PIN), freq=1000)
motor_p2 = PWM(Pin(IN2_PIN), freq=1000)

def stop():
    """Stops the motor by turning both pins off"""
    motor_p1.duty_u16(0)
    motor_p2.duty_u16(0)
    print("Motor Stopped")

def move_forward(speed):
    """
    Moves forward. 
    Speed is a number between 0 (Stop) and 65535 (Full Speed)
    """
    motor_p1.duty_u16(speed) # Power to Pin 1
    motor_p2.duty_u16(0)     # Ground to Pin 2
    print(f"Forward at speed {speed}")

def move_backward(speed):
    """Moves backward."""
    motor_p1.duty_u16(0)     # Ground to Pin 1
    motor_p2.duty_u16(speed) # Power to Pin 2
    print(f"Backward at speed {speed}")

# --- MAIN LOOP ---
try:
    while True:
        # 1. Full Speed Forward
        move_forward(65535)
        time.sleep(2)
        
        # 2. Slow Speed Forward (Half Speed)
        move_forward(30000)
        time.sleep(2)
        
        # 3. Stop
        stop()
        time.sleep(1)
        
        # 4. Backward
        move_backward(65535)
        time.sleep(2)
        
        stop()
        time.sleep(1)

except KeyboardInterrupt:
    stop()