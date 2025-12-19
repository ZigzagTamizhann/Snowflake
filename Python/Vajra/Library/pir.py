from machine import Pin

class PIR:
    def __init__(self, pin_id):
        """
        Initialize the PIR Motion Sensor.
        :param pin_id: The GPIO pin number connected to the sensor's OUT pin.
        """
        # Set the pin as an INPUT so we can read from it
        # PULL_DOWN ensures the pin stays low (0) when there is no signal
        self.pin = Pin(pin_id, Pin.IN, Pin.PULL_DOWN)

    def is_active(self):
        """
        Check if motion is currently detected.
        Returns: True if motion detected, False otherwise.
        """
        return self.pin.value() == 1
    