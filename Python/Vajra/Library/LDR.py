from machine import ADC

class LDR:
    def __init__(self, pin_id):
        """
        Initialize the LDR sensor.
        :param pin_id: The GPIO pin number connected to the LDR (must be an ADC pin).
        """
        # Initialize the Analog-to-Digital Converter on the specified pin
        self.adc = ADC(pin_id)

    def read_raw(self):
        """
        Reads the raw 16-bit integer value from the sensor.
        Range: 0 (Dark) to 65535 (Bright) - *Note: exact mapping depends on wiring.
        """
        return self.adc.read_u16()

    def read_percentage(self):
        """
        Converts the raw reading to a percentage (0% to 100%).
        Useful for readability.
        """
        raw_value = self.read_raw()
        # Convert 16-bit value (0-65535) to percentage
        percentage = (raw_value / 65535) * 100
        return round(percentage, 2)