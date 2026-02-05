import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore
import random

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed):
        """Initializes the motor driver pins using PWM for speed control."""
        # Initialize pins as PWM objects
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        # Set a common frequency for all motor PWM pins
        freq = 1000
        self.motor_a1.freq(freq)
        self.motor_a2.freq(freq)
        self.motor_b1.freq(freq)
        self.motor_b2.freq(freq)

        # Set the speed (duty cycle)
        self.set_speed(speed)

        self.stop()

    def set_speed(self, speed):
        """Sets motor speed. speed is a value between 0.0 and 1.0."""
        speed = max(0.0, min(1.0, speed)) # Clamp speed between 0 and 1
        self.duty_cycle = int(speed * 65535)
        
        # Set a separate, max-speed duty cycle for turning
        self.turn_duty_cycle = int(0.8 * 65535)

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

    def backward_left(self):
        """Moves backward and to the left by stopping the left wheel and reversing the right."""
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)  # Stop left wheel
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(self.turn_duty_cycle)  # Reverse right wheel

    def backward_right(self):
        """Moves backward and to the right by reversing the left wheel and stopping the right."""
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(self.turn_duty_cycle)  # Reverse left wheel
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)  # Stop right wheel

    def stop(self):
        self.motor_a1.duty_u16(0)
        self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0)
        self.motor_b2.duty_u16(0)

class IRSensor:
    def __init__(self, left_pin, right_pin):
        """Initializes the IR sensor pins."""
        self.left_ir_pin = Pin(left_pin, Pin.IN)
        self.right_ir_pin = Pin(right_pin, Pin.IN)

    def read_line(self):
        """
        Reads the state of the left and right IR sensors.
        Returns a tuple (left_value, right_value).
        Typically, 0 means a black line is detected, and 1 means a white surface.
        """
        return (self.left_ir_pin.value(), self.right_ir_pin.value())

class LED:
    def __init__(self, num_leds):
        """Initializes the LED strip."""
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        """Sets all LEDs to the same color."""
        for i in range(1, self.NUM_LEDS + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
        """Turns all LEDs off."""
        self.set_all(0, 0, 0)

# --- Hardware Initialization ---
motor = Motor(a1_pin=Subu.IO18, a2_pin=Subu.IO19, b1_pin=Subu.IO20, b2_pin=Subu.IO21, speed=0.40)
ir_sensor = IRSensor(left_pin=Subu.IO15, right_pin=Subu.IO13)
led = LED(num_leds=48)
   
print("Edge Avoiding Robot - Starting...")

# --- Main Program Loop ---
try:
    # Startup LED sequence
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

    while True:
        left_val, right_val = ir_sensor.read_line() # type: ignore
        
        if left_val == 0 and right_val == 0:
            led.set_all(0, 255, 0) # Green for Forward
            motor.forward()
            
        elif left_val == 0 and right_val == 1:
            led.set_all(0, 0, 255) # Blue for Turn Left
            motor.backward_left()
            time.sleep_ms(1500)
            
        elif left_val == 1 and right_val == 0:
            led.set_all(0, 0, 255) # Blue for Turn Right
            motor.backward_right()
            time.sleep_ms(1500)
            
        elif left_val == 1 and right_val == 1:
            print("Edge detected! Avoiding...")
            led.set_all(255, 0, 0) # Red for Stop/Backward
            motor.backward()
            time.sleep_ms(1000) # Back up for 0.5 seconds
            
            motor.stop() # Pause before turning
            time.sleep_ms(200)
            
            if random.choice([0, 1]) == 0:
                print("Turning left...")
                print("Moving backward and left...")
                led.set_all(255, 150, 0) # Yellow for avoidance turn
                motor.backward_left()
                time.sleep_ms(1500) # Move backward and turn for 0.8 seconds
                
            else:
                print("Turning right...")
                print("Moving backward and right...")
                led.set_all(255, 150, 0) # Yellow for avoidance turn
                motor.backward_right()
                time.sleep_ms(1500) # Move backward and turn for 0.8 seconds

            print("Moving forward to clear the edge...")
            print("Continuing forward...")
            led.set_all(0, 255, 0) # Green: Moving to safety
            motor.forward()
            time.sleep_ms(500) # Move forward for 0.5 seconds

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program stopped by user.")
    # Cleanly stop motors and turn off LEDs
    led.off() # type: ignore
    motor.stop()




