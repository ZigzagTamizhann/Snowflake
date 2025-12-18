import machine
from tcs3472 import tcs3472

bus = machine.I2C(sda=machine.Pin(4), scl=machine.Pin(5)) # adjust pin numbers as per hardware
tcs = tcs3472(bus)

print("Light:", tcs.light())
print("RGB:", tcs.rgb())