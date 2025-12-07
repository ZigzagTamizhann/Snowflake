import time
from machine import Pin, PWM, time_pulse_us # type: ignore
import Snowflake # type: ignore
import urandom # type: ignore

class Motor:
    """மோட்டார்களைக் கட்டுப்படுத்தும் கிளாஸ்."""
    def __init__(self, a1_pin, a2_pin, b1_pin, b2_pin, speed, turn_speed):
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

class LED:
    """LED-களைக் கட்டுப்படுத்தும் கிளாஸ்."""
    def __init__(self, num_leds):
        self.NUM_LEDS = num_leds

    def set_all(self, r, g, b):
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, (r, g, b))

    def set_disco_colors(self, colors):
        """ஒவ்வொரு LED-க்கும் பட்டியலில் இருந்து ஒரு சீரற்ற வண்ணத்தை அமைக்கிறது."""
        for i in range(1, self.NUM_LEDS + 1):
            Snowflake.setSingleLED(i, urandom.choice(colors))

    def off(self):
        self.set_all(0, 0, 0)

# --- வன்பொருள் பாகங்களை தொடங்குதல் ---
motor = Motor(a1_pin=Snowflake.IO17, a2_pin=Snowflake.IO18, b1_pin=Snowflake.IO19, b2_pin=Snowflake.IO20, speed=1.0, turn_speed=0.7)
led = LED(num_leds=9)

print("Dancing Robot - Starting...")

try:
    # தொடக்கத்தில் LED-களை ஒளிரச் செய்தல்
    for i in range(1, led.NUM_LEDS + 1):
        Snowflake.setSingleLED(i, (0, 0, 255))  # நீல நிறம்
        time.sleep_ms(50)
    time.sleep_ms(500)
    led.off()
    
    # பார்ட்டிக்கு ஏற்ற வண்ணங்களின் பட்டியல்
    PARTY_COLORS = [
        (150, 0, 255),  # Purple
        (255, 0, 150),  # Magenta
        (0, 100, 255),  # Neon Blue
        (0, 255, 255),  # Cyan
        (255, 50, 0),   # Orange-Red
    ]

    def shimmy():
        """இருபுறமும் வேகமாக அசைந்து நடனமாடும்."""
        print("Executing move: Shimmy")
        for _ in range(5): # அசைவுகளின் எண்ணிக்கையை அதிகரித்தல்
            led.set_disco_colors(PARTY_COLORS)
            motor.turn_left(); time.sleep_ms(200)
            motor.turn_right(); time.sleep_ms(200)
        motor.stop()

    def spin():
        """வேகமாக சுழலும் ஒரு டிஸ்கோ விளைவு."""
        print("Executing move: Spin")
        duration_ms = 1200 # சுழலும் நேரத்தை அதிகரித்தல்
        steps = 12
        if urandom.choice([True, False]):
            move = motor.turn_left
        else:
            move = motor.turn_right
        
        move()
        for _ in range(steps):
            led.set_disco_colors(PARTY_COLORS) # சுழலும்போது வண்ணங்களை மாற்றுகிறது
            time.sleep_ms(duration_ms // steps)
        motor.stop()

    def step_dance():
        """முன்னோக்கி மற்றும் பின்னோக்கி நடனமாடும்."""
        print("Executing move: Step Dance")
        led.set_disco_colors(PARTY_COLORS)
        motor.forward(); time.sleep_ms(150) # நேரத்தை மேலும் அதிகரித்தல்
        motor.backward(); time.sleep_ms(150)
        motor.stop()

    def cruise():
        """சீரான வேகத்தில் நகரும்."""
        print("Executing move: Cruise")
        led.set_disco_colors(PARTY_COLORS)
        if urandom.choice([True, False]):
            motor.forward()
        else:
            motor.backward()
        time.sleep_ms(urandom.randint(50, 150)) # நேரத்தை மேலும் அதிகரித்தல்
        motor.stop()

    def pulse_dance():
        """துடிப்புடன் முன்னோக்கி அல்லது பின்னோக்கி நகரும்."""
        print("Executing move: Pulse Dance")
        move = motor.forward if urandom.choice([True, False]) else motor.backward
        for _ in range(2): # துடிப்புகளின் எண்ணிக்கையை அதிகரித்தல்
            move(); led.set_disco_colors(PARTY_COLORS)
            time.sleep_ms(150) # ஒவ்வொரு துடிப்பின் நேரத்தையும் அதிகரித்தல்
            motor.stop(); led.off()
            time.sleep_ms(80)

    def curve_dance():
        """வளைந்து நடனமாடும்."""
        print("Executing move: Curve Dance")
        move = motor.turn_left if urandom.choice([True, False]) else motor.turn_right
        move()
        duration_ms = 1500 # வளைந்து செல்லும் நேரத்தை அதிகரித்தல்
        steps = 5
        for _ in range(steps):
            led.set_disco_colors(PARTY_COLORS)
            time.sleep_ms(duration_ms // steps)
        motor.stop()

    # புதிய நடன அசைவுகளின் பட்டியல்
    dance_moves = [shimmy, spin, step_dance, cruise, pulse_dance, curve_dance]

    # டான்ஸ் ஆடும் முக்கிய பகுதி
    while True:
        # நடன அசைவுகளின் ஒரு நகலை உருவாக்கவும்
        shuffled_moves = list(dance_moves)

        # Fisher-Yates shuffle அல்காரிதம் பயன்படுத்தி பட்டியலை சீரற்ற முறையில் வரிசைப்படுத்தவும்
        for i in range(len(shuffled_moves) - 1, 0, -1):
            j = urandom.randint(0, i)
            shuffled_moves[i], shuffled_moves[j] = shuffled_moves[j], shuffled_moves[i]

        # வரிசைப்படுத்தப்பட்ட பட்டியலில் உள்ள ஒவ்வொரு நடன அசைவையும் இயக்கவும்
        for dance_routine in shuffled_moves:
            dance_routine()
            time.sleep_ms(10) # அடுத்த அசைவுக்கு முன் சிறிய இடைவெளி

except KeyboardInterrupt:
    print("Program stopped by user.")
    motor.stop()
    led.off()
