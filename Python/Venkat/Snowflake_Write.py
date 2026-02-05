from machine import Pin
from time import sleep
import Subu

# -------------------------
# MOTOR PIN SETUP
# -------------------------
left1  = Pin(Subu.IO17, Pin.OUT)   # IN1
left2  = Pin(Subu.IO18, Pin.OUT)   # IN2
right1 = Pin(Subu.IO19, Pin.OUT)   # IN3
right2 = Pin(Subu.IO20, Pin.OUT)   # IN4

def stop():
    left1.low(); left2.low()
    right1.low(); right2.low()

def forward(t):
    # both sides forward
    left1.high(); left2.low()
    right1.high(); right2.low()
    sleep(t)
    stop()

def turn_right(t):
    # left forward, right backward → rotate right
    left1.high(); left2.low()
    right1.low(); right2.high()
    sleep(t)
    stop()

# -------------------------
# MAIN: DRAW ONE SQUARE
# -------------------------

SIDE_TIME = 1.5   # seconds to move one side
TURN_TIME = 0.55  # seconds to turn ~90 degrees

print("Drawing square...")

for i in range(4):
    forward(SIDE_TIME)     # move straight
    sleep(0.2)
    turn_right(TURN_TIME)  # turn 90 degree
    sleep(0.2)

stop()
print("Done.")
