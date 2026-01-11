import time
from machine import Pin, PWM, UART # type: ignore
import Snowflake # type: ignore

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
        speed_fraction = max(0.2, min(1.0, speed_fraction))
        self.duty_cycle = int(speed_fraction * 65535)
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
        for i in range(1, self.NUM_LEDS + 1): Snowflake.setSingleLED(i, (r, g, b))

    def off(self): self.set_all(0, 0, 0)

# --- Hardware and Communication Setup ---
motor = Motor(a1_pin=Snowflake.IO1, a2_pin=Snowflake.IO2, b1_pin=Snowflake.IO3, b2_pin=Snowflake.IO4)
led = LED()
uart = UART(0, baudrate=115200, tx=Snowflake.IO13, rx=Snowflake.IO14)

def main():
    print("Measuring Bot Receiver: Ready for commands.")
    led.set_all(0, 0, 255); time.sleep(1); led.off()

    while True:
        if uart.any():
            command_bytes = uart.readline()
            if command_bytes:
                command = command_bytes.decode('utf-8').strip()
                print(f"Received: '{command}'")

                if command == 'F': motor.forward(); led.set_all(0, 255, 0)
                elif command == 'B': motor.backward(); led.set_all(255, 100, 0)
                elif command == 'L': motor.turn_left(); led.set_all(0, 0, 255)
                elif command == 'R': motor.turn_right(); led.set_all(0, 0, 255)
                elif command == 'S': motor.stop(); led.set_all(255, 0, 0)
                elif command.startswith('V'):
                    try:
                        speed_fraction = int(command[1:]) / 100.0
                        motor.set_speed(speed_fraction)
                    except (ValueError, IndexError):
                        print("Invalid speed command.")
        time.sleep_ms(20)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        motor.stop(); led.off()
        print("Cleanup complete.")