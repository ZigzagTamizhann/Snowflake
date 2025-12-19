from machine import Pin, I2C # type: ignore
import framebuf# type: ignore
import time
import Subu # type: ignore

# =========================================
# SH1106 Driver Class
# =========================================
class SH1106(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C, rotate=0):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        self.write_cmd(0xAE)  # Display OFF
        self.write_cmd(0xA1)  # Segment remap
        self.write_cmd(0xC8)  # COM Output Scan Direction
        self.write_cmd(0xA8)  # Multiplex ratio
        self.write_cmd(0x3F)  # Duty cycle (1/64)
        self.write_cmd(0xD3)  # Display offset
        self.write_cmd(0x00)
        self.write_cmd(0xD5)  # Oscillator frequency
        self.write_cmd(0x80)
        self.write_cmd(0xD9)  # Pre-char3ge period
        self.write_cmd(0x22)
        self.write_cmd(0xDA)  # COM hardware config
        self.write_cmd(0x12)
        self.write_cmd(0xDB)  # VCOM deselect level
        self.write_cmd(0x40)
        self.write_cmd(0x81)  # Contrast control
        self.write_cmd(0xFF)
        self.write_cmd(0xA4)  # Entire display ON
        self.write_cmd(0xA6)  # Normal display
        self.write_cmd(0xAF)  # Display ON

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def show(self):
        # SH1106 requires writing page by page
        for page in range(self.pages):
            # 0xB0 + page = set page address
            # 0x02 = set lower column address (offset by 2 pixels for most SH1106)
            # 0x10 = set higher column address
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x02) 
            self.write_cmd(0x10)
            
            # Write the data for this page
            # 0x40 is the data byte flag
            start_index = self.width * page
            end_index = self.width * (page + 1)
            self.i2c.writeto(self.addr, b'\x40' + self.buffer[start_index:end_index])

# =========================================
# Main Code
# =========================================

# Subu pins
i2c_sda = Pin(Subu.IO3)
i2c_scl = Pin(Subu.IO4)

# Initialize I2C
# freq=400000 is standard speed
i2c = I2C(0, scl=i2c_scl, sda=i2c_sda, freq=400000)

print("Scanning I2C...")
devices = i2c.scan()
print("I2C devices:", devices)

if devices:
    # Use the first device found (usually 60 / 0x3C)
    addr = devices[0]
    print(f"Connecting to device at {hex(addr)}")
    
    try:
        # Initialize SH1106 Driver
        oled = SH1106(128, 64, i2c, addr=addr)

        # Clear and Draw
        oled.fill(0)
        oled.text("Hello Subu!", 5, 5)
        oled.text("I am SH1106", 5, 20)
        
        oled.show()
        print("Display updated!")
        
    except Exception as e:
        print(f"Error initializing display: {e}")
else:
    print("No OLED found. Check wiring!")