from machine import Pin, SPI
import time

CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_BIT_MODIFY = 0x05
CMD_RTS_TXB0 = 0x81

REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F
REG_CNF3 = 0x28
REG_CNF2 = 0x29
REG_CNF1 = 0x2A
REG_CANINTF = 0x2C
REG_TXB0CTRL = 0x30
REG_TXB0SIDH = 0x31
REG_TXB0SIDL = 0x32
REG_TXB0DLC = 0x35
REG_TXB0D0 = 0x36

MODE_NORMAL = 0x00

CAN_ID_SPEED = 0x100
CAN_ID_RPM = 0x200
CAN_ID_BATTERY = 0x300
CAN_ID_BRAKE = 0x400
CAN_ID_COOLANT = 0x500

cs = Pin(5, Pin.OUT)
cs.value(1)

spi = SPI(
    2,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(23),
    miso=Pin(19),
)


def command(value):
    cs.value(0)
    spi.write(bytearray([value]))
    cs.value(1)


def write_register(address, value):
    cs.value(0)
    spi.write(bytearray([CMD_WRITE, address, value & 0xFF]))
    cs.value(1)


def read_register(address):
    cs.value(0)
    spi.write(bytearray([CMD_READ, address]))
    value = spi.read(1)[0]
    cs.value(1)
    return value


def bit_modify(address, mask, value):
    cs.value(0)
    spi.write(bytearray([CMD_BIT_MODIFY, address, mask, value]))
    cs.value(1)


def set_mode(mode):
    bit_modify(REG_CANCTRL, 0xE0, mode)
    time.sleep(0.1)


def configure_125kbps_8mhz():
    # Sender and receiver must use the same CAN bit timing.
    write_register(REG_CNF1, 0x03)
    write_register(REG_CNF2, 0xF0)
    write_register(REG_CNF3, 0x86)


def write_standard_id(can_id):
    # Load an 11-bit standard CAN ID into TX buffer 0.
    write_register(REG_TXB0SIDH, (can_id >> 3) & 0xFF)
    write_register(REG_TXB0SIDL, (can_id & 0x07) << 5)


def setup_can():
    command(CMD_RESET)
    time.sleep(0.1)
    configure_125kbps_8mhz()
    set_mode(MODE_NORMAL)
    print("CANCTRL:", hex(read_register(REG_CANCTRL)))
    print("CANSTAT:", hex(read_register(REG_CANSTAT)))


def send_frame(can_id, value):
    # This project sends one-byte demo signals, so DLC is always 1.
    write_register(REG_CANINTF, 0x00)
    write_register(REG_TXB0CTRL, 0x00)
    write_standard_id(can_id)
    write_register(REG_TXB0DLC, 1)
    write_register(REG_TXB0D0, value)
    command(CMD_RTS_TXB0)
    time.sleep(0.05)


def send_and_print(can_id, name, value):
    send_frame(can_id, value)
    print("Sent ID:", hex(can_id), "|", name + ":", value)


print("Sender ECU started")
setup_can()

# The first three frames match the expected receiver output in the README.
test_frames = [
    (CAN_ID_SPEED, "Speed", 40),
    (CAN_ID_SPEED, "Speed", 80),
    (CAN_ID_SPEED, "Speed", 255),
    (CAN_ID_RPM, "RPM", 120),
    (CAN_ID_RPM, "RPM", 250),
    (CAN_ID_BATTERY, "Battery", 12),
    (CAN_ID_BATTERY, "Battery", 9),
    (CAN_ID_BRAKE, "Brake", 1),
    (CAN_ID_BRAKE, "Brake", 3),
    (CAN_ID_COOLANT, "Coolant", 90),
    (CAN_ID_COOLANT, "Coolant", 130),
]

while True:
    for can_id, name, value in test_frames:
        send_and_print(can_id, name, value)
        time.sleep(1)
