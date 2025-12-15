from machine import Pin, time_pulse_us
import time

#vajra-include-begin Ultrasonic

class Ultrasonic:
    """Measures distance using an HC-SR04 ultrasonic sensor."""
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def get_distance_cm(self):
        self.trigger.value(0); time.sleep_us(2)
        self.trigger.value(1); time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_duration = time_pulse_us(self.echo, 1, 30000) # 30ms timeout
            return (pulse_duration * 0.0343) / 2
        except OSError:
            return -1
