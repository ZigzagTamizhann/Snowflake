import time
from IR import IR
import Subu # type: ignore

# Define the GPIO pin connected to the IR sensor
IR_PIN = Subu.IO2

test_ir = IR(IR_PIN)

while True:
    if test_ir.is_detected():
        print("True")
    else:
        print("False")
    time.sleep(0.5)
