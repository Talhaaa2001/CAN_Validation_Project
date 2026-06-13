from machine import Pin, SPI
import time

# MCP2515 SPI commands.
CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_BIT_MODIFY = 0x05
CMD_RTS_TXB0 = 0x81

# MCP2515 registers used by this test.
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
REG_RXB0CTRL = 0x60
REG_RXB0SIDH = 0x61
REG_RXB0SIDL = 0x62
REG_RXB0DLC = 0x65
REG_RXB0D0 = 0x66

MODE_LOOPBACK = 0x40

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
    spi.write(bytearray([CMD_WRITE, address, value]))
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
    # CANCTRL bits 7:5 request the MCP2515 operating mode.
    bit_modify(REG_CANCTRL, 0xE0, mode)
    time.sleep(0.1)


def configure_125kbps_8mhz():
    # Common timing for MCP2515 modules with an 8 MHz crystal at 125 kbps.
    write_register(REG_CNF1, 0x03)
    write_register(REG_CNF2, 0xF0)
    write_register(REG_CNF3, 0x86)


def write_standard_id(base_register, can_id):
    # Standard 11-bit CAN ID is split across SIDH and SIDL.
    write_register(base_register, (can_id >> 3) & 0xFF)
    write_register(base_register + 1, (can_id & 0x07) << 5)


print("Starting CAN loopback test")

command(CMD_RESET)
time.sleep(0.1)
configure_125kbps_8mhz()
write_register(REG_RXB0CTRL, 0x60)  # Accept any standard data frame in RXB0.
set_mode(MODE_LOOPBACK)

print("CANCTRL:", hex(read_register(REG_CANCTRL)))
print("CANSTAT:", hex(read_register(REG_CANSTAT)))

# Clear old interrupt flags and load TX buffer 0 with CAN ID 0x100, DLC 1, DATA0 25.
write_register(REG_CANINTF, 0x00)
write_register(REG_TXB0CTRL, 0x00)
write_standard_id(REG_TXB0SIDH, 0x100)
write_register(REG_TXB0DLC, 1)
write_register(REG_TXB0D0, 25)

# Request transmission. In loopback mode the MCP2515 receives its own frame.
command(CMD_RTS_TXB0)
time.sleep(0.2)

canintf = read_register(REG_CANINTF)
rx_sidh = read_register(REG_RXB0SIDH)
rx_sidl = read_register(REG_RXB0SIDL)
rx_dlc = read_register(REG_RXB0DLC) & 0x0F
rx_data0 = read_register(REG_RXB0D0)
rx_id = (rx_sidh << 3) | (rx_sidl >> 5)

print("CANINTF:", hex(canintf))
print("Received ID:", hex(rx_id))
print("Received DLC:", rx_dlc)
print("Received DATA0:", rx_data0)

if rx_id == 0x100 and rx_dlc == 1 and rx_data0 == 25:
    print("CAN LOOPBACK PASS")
else:
    print("CAN LOOPBACK FAIL")
