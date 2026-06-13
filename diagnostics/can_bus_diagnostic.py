from machine import Pin, SPI
import time

CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_BIT_MODIFY = 0x05

REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F
REG_TEC = 0x1C
REG_REC = 0x1D
REG_CNF3 = 0x28
REG_CNF2 = 0x29
REG_CNF1 = 0x2A
REG_CANINTF = 0x2C
REG_EFLG = 0x2D
REG_RXB0CTRL = 0x60
REG_RXB1CTRL = 0x70

MODE_NORMAL = 0x00
MODE_LISTEN_ONLY = 0x60

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
    write_register(REG_CNF1, 0x03)
    write_register(REG_CNF2, 0xF0)
    write_register(REG_CNF3, 0x86)


def print_status(label):
    print(
        label,
        "| CANSTAT:",
        hex(read_register(REG_CANSTAT)),
        "| CANCTRL:",
        hex(read_register(REG_CANCTRL)),
        "| CANINTF:",
        hex(read_register(REG_CANINTF)),
        "| EFLG:",
        hex(read_register(REG_EFLG)),
        "| TEC:",
        read_register(REG_TEC),
        "| REC:",
        read_register(REG_REC),
    )


print("CAN bus diagnostic")
print("This uses listen-only mode, so it will not transmit ACK/error frames.")

command(CMD_RESET)
time.sleep(0.1)
configure_125kbps_8mhz()
write_register(REG_RXB0CTRL, 0x64)
write_register(REG_RXB1CTRL, 0x60)
write_register(REG_CANINTF, 0x00)
set_mode(MODE_LISTEN_ONLY)

print_status("start")

for i in range(1, 11):
    time.sleep(1)
    print_status("second " + str(i))

print("Diagnostic finished")
