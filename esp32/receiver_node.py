from machine import I2C, Pin, SPI
import time

CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_BIT_MODIFY = 0x05

REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F
REG_CNF3 = 0x28
REG_CNF2 = 0x29
REG_CNF1 = 0x2A
REG_CANINTF = 0x2C
REG_EFLG = 0x2D
REG_TEC = 0x1C
REG_REC = 0x1D
REG_RXB0CTRL = 0x60
REG_RXB0SIDH = 0x61
REG_RXB0SIDL = 0x62
REG_RXB0DLC = 0x65
REG_RXB0D0 = 0x66
REG_RXB1CTRL = 0x70
REG_RXB1SIDH = 0x71
REG_RXB1SIDL = 0x72
REG_RXB1DLC = 0x75
REG_RXB1D0 = 0x76

MODE_NORMAL = 0x00

OLED_ENABLED = True
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SDA_PIN = 21
OLED_SCL_PIN = 22
OLED_I2C_ADDR = 0x3C

CAN_ID_SPEED = 0x100
CAN_ID_RPM = 0x200
CAN_ID_BATTERY = 0x300
CAN_ID_BRAKE = 0x400
CAN_ID_COOLANT = 0x500

VALID_CAN_IDS = (
    CAN_ID_SPEED,
    CAN_ID_RPM,
    CAN_ID_BATTERY,
    CAN_ID_BRAKE,
    CAN_ID_COOLANT,
)

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

oled = None


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
    # Must match sender timing. These values are common for 8 MHz MCP2515 boards.
    write_register(REG_CNF1, 0x03)
    write_register(REG_CNF2, 0xF0)
    write_register(REG_CNF3, 0x86)


def setup_can():
    command(CMD_RESET)
    time.sleep(0.1)
    configure_125kbps_8mhz()

    # Accept all valid standard/extended frames in hardware, then filter our
    # demo IDs in software. RXB0 rollover lets RXB1 catch a second frame.
    write_register(REG_RXB0CTRL, 0x64)
    write_register(REG_RXB1CTRL, 0x60)

    # Clear old flags so stale RX0IF/RX1IF bits do not make us read garbage.
    write_register(REG_CANINTF, 0x00)
    set_mode(MODE_NORMAL)
    print("CANCTRL:", hex(read_register(REG_CANCTRL)))
    print("CANSTAT:", hex(read_register(REG_CANSTAT)))


def setup_oled():
    global oled

    if not OLED_ENABLED:
        return

    try:
        from ssd1306 import SSD1306_I2C

        i2c = I2C(
            0,
            scl=Pin(OLED_SCL_PIN),
            sda=Pin(OLED_SDA_PIN),
            freq=400000,
        )
        oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_I2C_ADDR)
        oled.fill(0)
        oled.text("CAN Receiver", 0, 0)
        oled.text("Waiting...", 0, 16)
        oled.show()
        print("OLED display ready")
    except Exception as exc:
        oled = None
        print("OLED not available:", exc)


def update_oled(can_id, signal, value, warning, result):
    if oled is None:
        return

    oled.fill(0)
    oled.text("CAN Validation", 0, 0)
    oled.hline(0, 10, OLED_WIDTH, 1)
    oled.text("ID " + hex(can_id), 0, 16)
    oled.text(signal + ":" + str(value), 0, 28)

    if warning != "N/A":
        oled.text("Warn:" + warning, 0, 40)
    else:
        oled.text("Warn:N/A", 0, 40)

    oled.text(result, 0, 52)
    oled.show()


def read_rx_buffer(base_register):
    # Decode the standard 11-bit CAN ID and first data byte from an RX buffer.
    sidh = read_register(base_register)
    sidl = read_register(base_register + 1)
    dlc_register = read_register(base_register + 4)
    data0 = read_register(base_register + 5)
    can_id = (sidh << 3) | (sidl >> 5)
    dlc = dlc_register & 0x0F
    is_extended = (sidl & 0x08) != 0
    is_remote = (dlc_register & 0x40) != 0
    return can_id, dlc, data0, is_extended, is_remote


def validate_frame(can_id, value):
    if can_id == CAN_ID_SPEED:
        warning = "ON" if value > 50 else "OFF"
        result = "PASS" if 0 <= value <= 250 else "FAIL"
        return "Speed", warning, result

    if can_id == CAN_ID_RPM:
        result = "PASS" if 0 <= value <= 200 else "FAIL"
        return "RPM", "N/A", result

    if can_id == CAN_ID_BATTERY:
        result = "PASS" if 10 <= value <= 15 else "FAIL"
        return "Battery", "N/A", result

    if can_id == CAN_ID_BRAKE:
        result = "PASS" if value == 0 or value == 1 else "FAIL"
        return "Brake", "N/A", result

    if can_id == CAN_ID_COOLANT:
        result = "PASS" if 70 <= value <= 110 else "FAIL"
        return "Coolant", "N/A", result

    return "Unknown", "N/A", "FAIL"


def print_result(can_id, signal, value, warning, result):
    if can_id == CAN_ID_SPEED:
        print(
            "Received ID:",
            hex(can_id),
            "| Speed:",
            value,
            "| Warning:",
            warning,
            "|",
            result,
        )
    else:
        print(
            "Received ID:",
            hex(can_id),
            "|",
            signal + ":",
            value,
            "|",
            result,
        )


print("Receiver ECU started")
setup_oled()
setup_can()

ignored_frames = 0
last_status_time = time.time()

while True:
    canintf = read_register(REG_CANINTF)
    processed_flags = 0

    if canintf & 0x01:
        rx_id, dlc, value, is_extended, is_remote = read_rx_buffer(REG_RXB0SIDH)

        if (
            dlc == 1
            and not is_extended
            and not is_remote
            and rx_id in VALID_CAN_IDS
        ):
            signal, warning, result = validate_frame(rx_id, value)
            print_result(rx_id, signal, value, warning, result)
            update_oled(rx_id, signal, value, warning, result)
        else:
            ignored_frames += 1

        processed_flags |= 0x01

    if canintf & 0x02:
        rx_id, dlc, value, is_extended, is_remote = read_rx_buffer(REG_RXB1SIDH)

        if (
            dlc == 1
            and not is_extended
            and not is_remote
            and rx_id in VALID_CAN_IDS
        ):
            signal, warning, result = validate_frame(rx_id, value)
            print_result(rx_id, signal, value, warning, result)
            update_oled(rx_id, signal, value, warning, result)
        else:
            ignored_frames += 1

        processed_flags |= 0x02

    if processed_flags:
        # Clear only the receive flags we consumed.
        write_register(REG_CANINTF, canintf & ~processed_flags)

    now = time.time()
    if ignored_frames and now - last_status_time >= 5:
        print(
            "Ignored non-demo frames:",
            ignored_frames,
            "| EFLG:",
            hex(read_register(REG_EFLG)),
            "| TEC:",
            read_register(REG_TEC),
            "| REC:",
            read_register(REG_REC),
        )
        ignored_frames = 0
        last_status_time = now

    time.sleep(0.05)
