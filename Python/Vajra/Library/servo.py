from machine import Pin, PWM # type: ignore
import time
import Subu # type: ignore

# ==========================================
# CONFIGURATION
# ==========================================
SERVO_PIN = Subu.IO2  # Change this to your pin
pwm = PWM(Pin(SERVO_PIN))
pwm.freq(50)  # Standard servo frequency is 50Hz

# ==========================================
# FUNCTION DEFINITION
# ==========================================
def set_angle(angle):
    """
    Moves the servo to the specified angle (0 to 180).
    """
    # Safety clamp: Ensure angle is between 0 and 180
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    # Calculation:
    # 0 degrees   = ~1638 duty (0.5ms pulse)
    # 180 degrees = ~8192 duty (2.5ms pulse)
    # We map the angle 0-180 to the duty range 1638-8192
    
    min_duty = 1638
    max_duty = 8192
    
    # This formula converts the angle into the correct duty cycle number
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    
    pwm.duty_u16(duty)
    print(f"Moving to {angle} degrees")

# ==========================================
# MAIN EXECUTION (The "Call")
# ==========================================

print("Servo Test Starting...")

# 1. Move to Center
set_angle(90)
time.sleep(1)

# 2. Move to 0
set_angle(0)
time.sleep(1)

# 3. Move to 180
set_angle(180)
time.sleep(1)

# 4. Sweep Function Demo
print("Sweeping...")
while True:
    # Sweep from 0 to 180
    for i in range(0, 181, 10): # Step by 10 degrees
        set_angle(i)
        time.sleep(0.05)
        
    # Sweep back from 180 to 0
    for i in range(180, -1, -10):
        set_angle(i)
        time.sleep(0.05)