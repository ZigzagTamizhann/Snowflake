import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed):
        """Initializes the motor driver pins using PWM for speed control."""
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        self.motor_a1.freq(freq)
        self.motor_a2.freq(freq)
        self.motor_b1.freq(freq)
        self.motor_b2.freq(freq)

        self.set_speed(speed)
        self.stop()

    def set_speed(self, speed):
        """Sets motor speed. speed is a value between 0.0 and 1.0."""
        speed = max(0.0, min(1.0, speed)) # Clamp speed between 0 and 1
        self.duty_cycle = int(speed * 65535)
        self.turn_duty_cycle = int(0.8 * 65535) # Separate, higher speed for turning

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle)
        self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        self.motor_a1.duty_u16(self.turn_duty_cycle)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.turn_duty_cycle)

    def turn_right(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle)
        self.motor_b2.duty_u16(0)

    def stop(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)


# --- Main Program ---
if __name__ == "__main__":
    # Initialize the motor with your specific pins and a default speed
    motor = Motor(a1_pin=Subu.IO18, a2_pin=Subu.IO19, b1_pin=Subu.IO20, b2_pin=Subu.IO21, speed=0.4)

    # --- IMPORTANT CALIBRATION STEP ---
    # You need to find the right 'turn_duration' for a 90-degree turn.
    # Uncomment the following linebv   `  s to test and find the right value.
    # print("Calibration: Testing a 0.5 second turn. Adjust as needed.")
    # motor.turn_right()
    # time.sleep(0.5) # Change this value (e.g., 0.4, 0.6) until it's a 90-degree turn
    # motor.stop()
    # time.sleep(3) # Pause to observe

    try:
        motor.forward()
        time.sleep(1.75)
        
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        # Cleanly stop motors
        motor.stop()
        print("Robot has stopped.")


