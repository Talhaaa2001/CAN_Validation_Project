from machine import Pin, SPI
import time
import random

cs = Pin(5, Pin.OUT)
cs.value(1)

spi = SPI(
    2,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(23),
    miso=Pin(19)
)

def cmd(c):
    cs.value(0)
    spi.write(bytearray([c]))
    cs.value(1)

def write_reg(addr, val):
    cs.value(0)
    spi.write(bytearray([0x02, addr, val]))
    cs.value(1)

def read_reg(addr):
    cs.value(0)
    spi.write(bytearray([0x03, addr]))
    val = spi.read(1)[0]
    cs.value(1)
    return val

def clear_interrupts():
    write_reg(0x2C, 0x00)

def setup_mcp2515_loopback():
    cmd(0xC0)
    time.sleep(0.1)

    # Loopback mode
    write_reg(0x0F, 0x40)
    time.sleep(0.1)

    print("CANCTRL:", hex(read_reg(0x0F)))
    print("CANSTAT:", hex(read_reg(0x0E)))

def send_speed(speed):
    # TX buffer 0, Standard ID 0x100
    write_reg(0x31, 0x20)  # TXB0SIDH
    write_reg(0x32, 0x00)  # TXB0SIDL

    write_reg(0x35, 1)     # DLC = 1 byte
    write_reg(0x36, speed) # DATA0 = speed

    cmd(0x81)              # Request send TXB0

def read_received_speed():
    rx_data0 = read_reg(0x66)
    return rx_data0

print("CAN Speed Validation Started")

setup_mcp2515_loopback()

while True:
    speed = random.choice([20, 40, 55, 80, 120, 255])

    clear_interrupts()
    send_speed(speed)
    time.sleep(0.2)

    received_speed = read_received_speed()

    warning = "ON" if received_speed > 50 else "OFF"
    result = "PASS" if 0 <= received_speed <= 250 else "FAIL"

    print(
        "CAN ID:0x100 | "
        "Sent Speed:" + str(speed) + " | "
        "Received Speed:" + str(received_speed) + " | "
        "Warning:" + warning + " | "
        + result
    )

    time.sleep(1)