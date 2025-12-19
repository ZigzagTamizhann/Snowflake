from machine import Pin # type: ignore

class IR:
    """
    Handles interaction with a digital IR obstacle sensor.
    """
    def __init__(self, pin_num, active_low=True):
        """
        Initialize the IR sensor.
        :param pin_num: GPIO pin number.
        :param active_low: Set to True if the sensor outputs 0 when an object is detected.
        """
        self.sensor = Pin(pin_num, Pin.IN)
        self.active_low = active_low

    def is_detected(self):
        """Returns True if an obstacle is detected, False otherwise."""
        if self.active_low:
            return self.sensor.value() == 0
        return self.sensor.value() == 1