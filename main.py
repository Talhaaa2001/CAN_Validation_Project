import time
import random

while True:
    temp = random.choice([22, 25, 27, 29, 255])

    print("Temperature:" + str(temp))

    time.sleep(1)