import time
import Subu
from Ultrasonic import Ultrasonic

sensor = Ultrasonic(Subu.IO1, Subu.IO2)

print("Starting Ultrasonic Distance Test...")

while True:
    distance = sensor.get_distance_cm()
    if distance != -1:
        print("Distance: {:.1f} cm".format(distance))
    else:
        print("Distance: Timeout")

    time.sleep(0.5)
