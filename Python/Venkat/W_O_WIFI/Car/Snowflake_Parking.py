import time
from machine import Pin, PWM # type: ignore
import Subu # type: ignore

class Motor:
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, Turn):
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
        self.set_speed(speed, Turn)

        self.stop()

    def set_speed(self, speed, Turn):
        """Sets motor speed. speed is a value between 0.0 and 1.0."""
        speed = max(0.0, min(1.0, speed)) # Clamp speed between 0 and 1
        self.duty_cycle = int(speed * 65535)
        
        # Set a separate, max-speed duty cycle for turning
        self.turn_duty_cycle = int(Turn * 65535)

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

In1 = Subu.IO18
In2 = Subu.IO19
In3 = Subu.IO20
In4 = Subu.IO21

speed = 0.4
Turn = 0.4

left_pin = Subu.IO1
right_pin = Subu.IO4

num_leds = 48


motor = Motor(In1, In2, In3, In4, speed, Turn)
ir_sensor = IRSensor(left_pin, right_pin)
led = LED(num_leds)
   
print("Line Following Robot - Starting...")

# --- Main Program Loop ---

try:
    
    for i in range(1, led.NUM_LEDS + 1):
        Subu.setSingleLED(i, (0, 0, 255))  # Blue
        time.sleep_ms(50)
    time.sleep_ms(1000)
    led.off()

    while True:
        # Read sensor values. Assuming 0 = Black Line, 1 = White Surface
        left_val, right_val = ir_sensor.read_line()

        print(f"Sensor values: Left={left_val}, Right={right_val}")

        # --- Line Following Logic ---

        # Case 1: Both sensors on white surface -> Move forward
        if left_val == 0 and right_val == 0:
            print("Forward")
            led.set_all(0, 255, 0)  # Green
            motor.forward()

        # Case 2: Left sensor on black line -> Turn left
        elif left_val == 1 and right_val == 0:
            print("Turn Left")
            led.set_all(255, 150, 0)  # Yellow
            motor.turn_left()

        # Case 3: Right sensor on black line -> Turn right
        elif left_val == 0 and right_val == 1:
            print("Turn Right")
            led.set_all(255, 150, 0)  # Yellow
            motor.turn_right()

        # Case 4: Both sensors on black line -> Initiate Sequential Parking Maneuver
        elif left_val == 1 and right_val == 1:
            count = 0
            print("Initial intersection detected. Starting parking sequence.")
            motor.stop()
            led.set_all(0, 255, 255) # Cyan to indicate parking mode
            time.sleep_ms(1000)

            # --- Parking Sequence Start ---

            # Step 1: Move forward to find the next intersection
            print("Step 1: Moving forward to find the next intersection...")
            motor.forward()
            time.sleep_ms(750)
            motor.stop()
            time.sleep_ms(1000)
            l, r = ir_sensor.read_line()
            if l == 1 and r == 1:
                count += 1

            # Step 2: Turn Right and find the next intersection
            print("Step 2: Turning right...")
            motor.turn_right()
            time.sleep_ms(200) 
            motor.stop()
            time.sleep_ms(1000)
            l, r = ir_sensor.read_line()
            if l == 1 and r == 1:
                count += 1

            # Step 3: Turn Left (1st time) and find the next intersection
            print("Step 3: Turning left (1/2)...")
            motor.turn_left()
            time.sleep_ms(400)
            motor.stop()
            time.sleep_ms(1000) # Adjust for a 90-degree turn
            l, r = ir_sensor.read_line()
            if l == 1 and r == 1:
                count += 1

            print("Step 4: Final turn right.")
            motor.turn_right()
            time.sleep_ms(200) # Adjust for a 90-degree turn
            
            if count == 3:
                # Step 5: Parked
                print("PARKED!")
                led.set_all(255, 0, 0)  # Solid Red to indicate parked
                l, r = ir_sensor.read_line()
                while l == 1 and r == 1:
                    motor.stop()
                time.sleep(1)
                
            
        time.sleep_ms(20)

except KeyboardInterrupt:
    print("Program stopped by user.")
    # Cleanly stop motors and turn off LEDs
    led.off()
    motor.stop()