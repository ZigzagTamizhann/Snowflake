# c:\venkat\thonny\Subu_WiFi_Control.py
import time
from machine import Pin, PWM, UART
import Subu

# --- Hardware Abstraction Classes ---

class Motor:
    """Controls the robot's motors using PWM for variable speed."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, initial_speed=0.5):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)

        self.set_speed(initial_speed)
        self.stop()

    def set_speed(self, speed_fraction):
        """Sets motor speed. speed_fraction is a value between 0.0 and 1.0."""
        # Clamp speed to a practical range (e.g., 20% min to avoid stalling)
        speed_fraction = max(0.2, min(1.0, speed_fraction))
        self.duty_cycle = int(speed_fraction * 65535)
        # Set turning speed to be slightly higher for responsiveness
        self.turn_duty_cycle = int(min(1.0, speed_fraction * 1.2) * 65535)
        print(f"Speed set to {int(speed_fraction * 100)}%")

    def forward(self):
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle); self.motor_b2.duty_u16(0)

    def turn_right(self):
        self.motor_a1.duty_u16(self.turn_duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty_cycle)

    def stop(self):
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)

class LED:
    """Controls the onboard NeoPixel-style LEDs."""
    def __init__(self, num_leds=9):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Subu.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- Hardware and Communication Setup ---
motor = Motor(
    a1_pin=Subu.IO3, a2_pin=Subu.IO5,
    b1_pin=Subu.IO3, b2_pin=Subu.IO6,
    initial_speed=0.5
)
led = LED()

# Configure UART to receive commands from the ESP32.
# Connect this board's RX pin (IO14) to the ESP32's TX pin (GPIO17).
# Connect this board's TX pin (IO13) to the ESP32's RX pin (GPIO16).
uart = UART(0, baudrate=115200, tx=Subu.IO1, rx=Subu.IO2)

# --- Main Program ---
def main():
    print("Subu WiFi Receiver: Ready for commands.")
    led.set_all(0, 0, 255) # Blue to indicate startup
    time.sleep(1)
    led.off()

    while True:
        if uart.any():
            command_bytes = uart.readline()
            if not command_bytes:
                continue

            command = command_bytes.decode('utf-8').strip()
            print(f"Received: '{command}'")

            # --- Command Processing ---
            if command == 'F':
                led.set_all(0, 255, 0) # Green for forward
                motor.forward()
            elif command == 'B':
                led.set_all(255, 100, 0) # Orange for backward
                motor.backward()
            elif command == 'L':
                led.set_all(0, 0, 255) # Blue for left
                motor.turn_left()
            elif command == 'R':
                led.set_all(0, 0, 255) # Blue for right
                motor.turn_right()
            elif command == 'S':
                led.set_all(255, 0, 0) 
                motor.stop()
            elif command.startswith('V'):
                try:
                    # Extract speed value (e.g., from 'V50')
                    speed_percent = int(command[1:])
                    speed_fraction = speed_percent / 100.0
                    motor.set_speed(speed_fraction)
                except (ValueError, IndexError):
                    print("Invalid speed command received.")
        
        # A small delay to prevent the loop from running too fast
        time.sleep_ms(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    finally:
        # Ensure motors and LEDs are turned off on exit
        motor.stop()
        led.off()
        print("Cleanup complete. Robot stopped.")
