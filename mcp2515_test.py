from machine import Pin, SPI
import time

# ESP32 to MCP2515 wiring used in this project.
CS_PIN = 5
SCK_PIN = 18
MOSI_PIN = 23
MISO_PIN = 19

CMD_RESET = 0xC0
CMD_READ = 0x03

REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F

cs = Pin(CS_PIN, Pin.OUT)
cs.value(1)

spi = SPI(
    2,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(SCK_PIN),
    mosi=Pin(MOSI_PIN),
    miso=Pin(MISO_PIN),
)


def reset_mcp2515():
    # Reset puts a healthy MCP2515 into configuration mode.
    cs.value(0)
    spi.write(bytearray([CMD_RESET]))
    cs.value(1)
    time.sleep(0.1)


def read_register(address):
    # MCP2515 register read command: command byte, address byte, then one byte back.
    cs.value(0)
    spi.write(bytearray([CMD_READ, address]))
    value = spi.read(1)[0]
    cs.value(1)
    return value


print("Starting MCP2515 SPI test...")

reset_mcp2515()

canstat = read_register(REG_CANSTAT)
canctrl = read_register(REG_CANCTRL)

print("CANSTAT:", hex(canstat))
print("CANCTRL:", hex(canctrl))

# After reset, CANSTAT normally reports 0x80 and CANCTRL often reports 0x87.
# The exact low bits of CANCTRL can vary, but the mode bits should be 0x80.
if (canstat & 0xE0) == 0x80 and (canctrl & 0xE0) == 0x80:
    print("MCP2515 SPI communication working")
else:
    print("No valid MCP2515 response - check wiring, power, CS, and SPI pins")
