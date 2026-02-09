import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore

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
        self.turn_duty_cycle = int(0.5 * 65535)

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
motor = Motor(a1_pin=Subu.IO5, a2_pin=Subu.IO6, b1_pin=Subu.IO8, b2_pin=Subu.IO7, speed=0.40)
ir_sensor = IRSensor(left_pin=Subu.IO2, right_pin=Subu.IO4)
led = LED(num_leds=48)
   
print("Line Following Robot - Starting...")

# --- Main Program Loop ---
try:
    
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

    while True:
        
        left_val, right_val = ir_sensor.read_line() # type: ignore
        
        print(f"Sensor values: Left={left_val}, Right={right_val}")

        # --- Line Following Logic ---

        # Case 1: Both sensors on white surface -> Move forward
        if left_val == 0 and right_val == 0:
            print("Forward")
            led.set_all(0, 255, 0)  # Green # type: ignore
            motor.forward()

        # Case 2: Right sensor on black line -> Turn right
        elif left_val == 0 and right_val == 1:
            print("Turn Left")
            led.set_all(255, 150, 0)  # Yellow # type: ignore
            motor.turn_left()
            time.sleep_ms(50)
        
        # Case 3: Left sensor on black line -> Turn left
        elif left_val == 1 and right_val == 0:
            print("Turn Right")
            led.set_all(255, 150, 0)  # Yellow # type: ignore
            motor.turn_right()
            time.sleep_ms(50)

        # Case 4: Both sensors on black line (e.g., intersection or end) -> Stop
        elif left_val == 1 and right_val == 1:
            print("Line end or intersection. Stopping.")
            led.set_all(255, 0, 0)  # Red # type: ignore
            motor.stop()
            time.sleep_ms(5000)
            motor.forward()
            time.sleep_ms(50)

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program stopped by user.")
    # Cleanly stop motors and turn off LEDs
    led.off() # type: ignore
    motor.stop()








