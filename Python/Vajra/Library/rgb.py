from machine import I2C, Pin
import time
import struct
import Subu

# --- Configuration ---
# Update these pins for your specific board!
# ESP32 Defaults: SDA=21, SCL=22
# RP2040 (Pico) Defaults: SDA=0, SCL=1
I2C_SDA_PIN = Subu.IO3
I2C_SCL_PIN = Subu.IO2
I2C_ID = 0 

# TCS34725 Address and Registers
SENSOR_ADDR = 0x29
ENABLE_REG = 0x00
CDATA_REG  = 0x14 # Clear data start register
COMMAND_BIT = 0x80

def init_sensor(i2c):
    """Initializes the sensor by powering it on."""
    # Write 0x03 (Power ON + ADC Enable) to the Enable Register
    # We must OR the register with COMMAND_BIT (0x80) for this sensor
    i2c.writeto_mem(SENSOR_ADDR, ENABLE_REG | COMMAND_BIT, b'\x03')
    # Wait a bit for the sensor to warm up
    time.sleep(0.1)

def read_rgbc(i2c):
    """Reads 8 bytes (Clear, Red, Green, Blue) and returns them."""
    # Read 8 bytes starting from the Clear Data Register
    # Data comes in Low Byte / High Byte order
    data = i2c.readfrom_mem(SENSOR_ADDR, CDATA_REG | COMMAND_BIT, 8)
    
    # Unpack data: 'H' means unsigned short (2 bytes)
    clear, red, green, blue = struct.unpack('<HHHH', data)
    return clear, red, green, blue

# --- Main Setup ---
try:
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
    print("I2C Initialized. Scanning...")
    
    devices = i2c.scan()
    if SENSOR_ADDR not in devices:
        print(f"Error: Sensor not found at address {hex(SENSOR_ADDR)}")
    else:
        print("Sensor found! Initializing...")
        init_sensor(i2c)
        
        while True:
            c, r, g, b = read_rgbc(i2c)
            print(f"Clear: {c}, Red: {r}, Green: {g}, Blue: {b}")
            time.sleep(1)

except Exception as e:
    print("An error occurred:", e)