from machine import Pin, SPI

CMD_READ = 0x03

REG_TEC = 0x1C
REG_REC = 0x1D
REG_CNF3 = 0x28
REG_CNF2 = 0x29
REG_CNF1 = 0x2A
REG_CANINTF = 0x2C
REG_EFLG = 0x2D
REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F

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


def read_register(address):
    cs.value(0)
    spi.write(bytearray([CMD_READ, address]))
    value = spi.read(1)[0]
    cs.value(1)
    return value


print("MCP2515 status")
print("CANSTAT:", hex(read_register(REG_CANSTAT)))
print("CANCTRL:", hex(read_register(REG_CANCTRL)))
print("CNF1:", hex(read_register(REG_CNF1)))
print("CNF2:", hex(read_register(REG_CNF2)))
print("CNF3:", hex(read_register(REG_CNF3)))
print("CANINTF:", hex(read_register(REG_CANINTF)))
print("EFLG:", hex(read_register(REG_EFLG)))
print("TEC:", read_register(REG_TEC))
print("REC:", read_register(REG_REC))

if (
    read_register(REG_CNF1) == 0x03
    and read_register(REG_CNF2) == 0xF0
    and read_register(REG_CNF3) == 0x86
):
    print("Bit timing registers match project setting: 125 kbps for 8 MHz MCP2515")
else:
    print("Bit timing registers do NOT match the project setting")
