import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Snowflake # type: ignore
import urandom

class Motor:
    """மோட்டார்களைக் கட்டுப்படுத்தும் கிளாஸ்."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed=0.5, turn_speed=0.8):
        self.motor_a1 = PWM(Pin(a1_pin))
        self.motor_a2 = PWM(Pin(a2_pin))
        self.motor_b1 = PWM(Pin(b1_pin))
        self.motor_b2 = PWM(Pin(b2_pin))

        freq = 1000
        for m in [self.motor_a1, self.motor_a2, self.motor_b1, self.motor_b2]:
            m.freq(freq)

        self.set_speed(speed, turn_speed)
        self.stop()

    def set_speed(self, speed, turn_speed):
        """மோட்டாரின் வேகம் மற்றும் திரும்பும் வேகத்தை அமைக்கிறது."""
        self.duty_cycle = int(max(0.0, min(1.0, speed)) * 65535)
        self.turn_duty_cycle = int(max(0.0, min(1.0, turn_speed)) * 65535)

    def forward(self):
        """முன்னோக்கி நகர்த்தும்."""
        self.motor_a1.duty_u16(self.duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(self.duty_cycle); self.motor_b2.duty_u16(0)

    def backward(self):
        """பின்னோக்கி நகர்த்தும்."""
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.duty_cycle)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.duty_cycle)

    def turn_left(self):
        """இடதுபுறம் திருப்பும்."""
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(self.turn_duty_cycle)
        self.motor_b1.duty_u16(self.turn_duty_cycle); self.motor_b2.duty_u16(0)

    def turn_right(self):
        """வலதுபுறம் திருப்பும்."""
        self.motor_a1.duty_u16(self.turn_duty_cycle); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(self.turn_duty_cycle)

    def stop(self):
        """மோட்டார்களை நிறுத்தும்."""
        self.motor_a1.duty_u16(0); self.motor_a2.duty_u16(0)
        self.motor_b1.duty_u16(0); self.motor_b2.duty_u16(0)

class IRSensor:
    """IR சென்சார்களைப் படிக்கும் கிளாஸ்."""
    def __init__(self, left_pin, right_pin):
        self.left_ir_pin = Pin(left_pin, Pin.IN)
        self.right_ir_pin = Pin(right_pin, Pin.IN)

    def read_values(self):
        # 0 என்றால் பொருள் அருகில் உள்ளது என்று அர்த்தம்
        return (self.left_ir_pin.value(), self.right_ir_pin.value())

class Ultrasonic:
    """அல்ட்ராசோனிக் சென்சார் மூலம் தூரத்தைக் கண்டறியும் கிளாஸ்."""
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def distance_cm(self):
        """தூரத்தை சென்டிமீட்டரில் வழங்கும்."""
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time_pulse_us(self.echo, 1, 30000)  # 30ms timeout
            if pulse_duration < 0:
                return float('inf')
            distance = (pulse_duration * 0.0343) / 2
            return distance
        except OSError:
            return float('inf')

class LED:
    """LED-களைக் கட்டுப்படுத்தும் கிளாஸ்."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, (r, g, b))

    def off(self):
        self.set_all(0, 0, 0)

# --- வன்பொருள் பாகங்களை தொடங்குதல் ---
motor = Motor(a1_pin=Snowflake.IO1, a2_pin=Snowflake.IO2, b1_pin=Snowflake.IO3, b2_pin=Snowflake.IO4, speed=0.3, turn_speed=0.6)
led = LED(num_leds=9)

print("Dancing Robot - Starting...")

try:
    # தொடக்கத்தில் LED-களை ஒளிரச் செய்தல்
    for i in range(1, led.NUM_LEDS + 1):
        Snowflake.setSingleLED(i, (0, 0, 255))  # நீல நிறம்
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()

    # சாத்தியமான அசைவுகளின் பட்டியல்
    # 50% வாய்ப்பு முன்னோக்கி செல்ல, மற்ற அசைவுகளுக்கு சம வாய்ப்பு
    moves = [
        motor.forward, 
        motor.backward,
        motor.turn_left,
        motor.turn_right,
        motor.stop
    ]

    # டான்ஸ் ஆடும் முக்கிய பகுதி
    while True:
        # ஒரு சீரற்ற அசைவைத் தேர்ந்தெடுக்கவும்
        move = urandom.choice(moves)
        move()
        print(f"Executing move: {move.__name__}")

        # சீரற்ற வண்ணத்தை LED-களுக்கு அமைக்கவும்
        r = urandom.randint(0, 150)
        g = urandom.randint(0, 150)
        b = urandom.randint(0, 150)
        led.set_all(r, g, b)

        # இந்த அசைவை ஒரு சீரற்ற நேரத்திற்கு இயக்கவும்
        time.sleep_ms(urandom.randint(200, 600))

except KeyboardInterrupt:
    print("Program stopped by user.")
    motor.stop()
    led.off()
