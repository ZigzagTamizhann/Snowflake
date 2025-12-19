import Subu # type: ignore
from machine import Pin # type: ignore
import neopixel # type: ignore
import time

# --- Configuration ---
# 1. Set the GPIO pin connected to the LED strip's data line (DIN/DI)
LED_PIN = 14
# 2. Set the total number of LEDs in your strip/ring
NUM_LEDS = 42

# Initialize the NeoPixel object
# Pin is an output, NUM_LEDS is the count, and neopixel.GRB is the color order (most common)
np = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)

# --- Functions (Mirroring Subu's Commands) ---

def set_single_led(index, color):
    """
    Sets a single LED to a specific RGB color.
    Equivalent to: Subu.setSingleLED(index, color)
    """
    # Check if the index is valid
    if 0 <= index < NUM_LEDS:
        # The color tuple should be (R, G, B), e.g., (255, 255, 255) for white
        np[index] = color
        # Must call write() to push the data to the strip
        np.write()
        print(f"Set LED {index} to {color}")
    else:
        print(f"Error: Index {index} is out of range (0 to {NUM_LEDS - 1}).")

def set_all_leds(color):
    """
    Sets all LEDs to a specific RGB color.
    Equivalent to: Subu.setAllLED(color)
    """
    # Fill the entire strip with the specified color
    for i in range(NUM_LEDS):
        np[i] = color
    
    # Must call write() to push the data to the strip
    np.write()
    print(f"Set ALL {NUM_LEDS} LEDs to {color}")

# --- Main Demonstration ---

# 1. Turn all LEDs White (Translates Subu.setAllLED((255,255,255)))
print("\n--- Test 1: Set All LEDs to White ---")
set_all_leds((255, 255, 255))
time.sleep(1)

# 2. Turn all LEDs OFF (Clear the strip)
print("Clearing all LEDs...")
set_all_leds((0, 0, 0))
time.sleep(0.5)

# 3. Set a specific LED to White (Translates Subu.setSingleLED(20, (255,255,255)))
LED_INDEX_TO_SET = 20
print(f"\n--- Test 2: Set Single LED (Index {LED_INDEX_TO_SET}) to White ---")
set_single_led(LED_INDEX_TO_SET, (255, 255, 255))
time.sleep(2)

# 4. Cleanup
print("\nTurning off all LEDs for cleanup.")
set_all_leds((0, 0, 0))