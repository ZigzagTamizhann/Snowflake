from machine import Pin # type: ignore

class VibrationSensor:
    def __init__(self, pin_id):
        """
        Initialize the Vibration Sensor.
        """
        self.pin = Pin(pin_id, Pin.IN, Pin.PULL_DOWN)

    def set_callback(self, handler_function):
        """
        Sets up the Interrupt.
        :param handler_function: The function to run when vibration is detected.
        """
        # IRQ_RISING means "Trigger when signal goes from Low (0) to High (1)"
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=handler_function)