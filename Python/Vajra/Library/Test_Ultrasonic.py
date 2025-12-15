import time
import Snowflake
from Ultrasonic import Ultrasonic

sensor = Ultrasonic(Snowflake.IO9, Snowflake.IO10)

print("Starting Ultrasonic Distance Test...")

while True:
    distance = sensor.get_distance_cm()
    if distance != -1:
        print("Distance: {:.1f} cm".format(distance))
    else:
        print("Distance: Timeout")

    time.sleep(0.5)
