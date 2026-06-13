from machine import Pin, SPI
import time

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

def set_id_0x100_to_0x400(can_id):
    sidh = can_id >> 3
    sidl = (can_id & 0x07) << 5
    write_reg(0x31, sidh)
    write_reg(0x32, sidl)

def send_can(can_id, data):
    write_reg(0x2C, 0x00)      # clear interrupts
    set_id_0x100_to_0x400(can_id)
    write_reg(0x35, 1)         # DLC = 1 byte
    write_reg(0x36, data)      # DATA0
    cmd(0x81)                  # send TXB0
    time.sleep(0.2)

def read_rx():
    rx_sidh = read_reg(0x61)
    rx_sidl = read_reg(0x62)
    can_id = (rx_sidh << 3) | (rx_sidl >> 5)
    dlc = read_reg(0x65)
    data = read_reg(0x66)
    return can_id, dlc, data

def validate(can_id, data):
    if can_id == 0x100:   # Vehicle Speed
        if 0 <= data <= 250:
            return "PASS", "Vehicle speed valid"
        return "FAIL", "Vehicle speed out of range"

    if can_id == 0x200:   # Engine RPM simplified
        if 0 <= data <= 200:
            return "PASS", "Engine RPM valid"
        return "FAIL", "Engine RPM out of range"

    if can_id == 0x300:   # Battery Voltage simplified
        if 10 <= data <= 15:
            return "PASS", "Battery voltage valid"
        return "FAIL", "Battery voltage out of range"

    if can_id == 0x400:   # Brake Status
        if data in [0, 1]:
            return "PASS", "Brake status valid"
        return "FAIL", "Brake status invalid"

    if can_id == 0x500:   # Coolant Temperature
        if 70 <= data <= 110:
            return "PASS", "Coolant temperature valid"
        return "FAIL", "Coolant temperature out of range"

    return "FAIL", "Unknown CAN ID"

print("CAN Validation Test Suite Started")

cmd(0xC0)
time.sleep(0.1)

write_reg(0x0F, 0x40)  # loopback mode
time.sleep(0.1)

print("CANCTRL:", hex(read_reg(0x0F)))
print("CANSTAT:", hex(read_reg(0x0E)))

print("timestamp,can_id,signal,sent_data,received_id,received_data,dlc,result,reason")

test_cases = [
    (0x100, "Vehicle Speed", 40),
    (0x100, "Vehicle Speed", 255),
    (0x200, "Engine RPM", 120),
    (0x200, "Engine RPM", 250),
    (0x300, "Battery Voltage", 12),
    (0x300, "Battery Voltage", 30),
    (0x400, "Brake Status", 1),
    (0x400, "Brake Status", 5),
    (0x500, "Coolant Temperature", 90),
    (0x500, "Coolant Temperature", 130),
]

for can_id, signal, data in test_cases:
    send_can(can_id, data)
    rx_id, dlc, rx_data = read_rx()

    result, reason = validate(rx_id, rx_data)

    print(
        str(time.time()) + "," +
        hex(can_id) + "," +
        signal + "," +
        str(data) + "," +
        hex(rx_id) + "," +
        str(rx_data) + "," +
        str(dlc) + "," +
        result + "," +
        reason
    )

    time.sleep(1)

print("CAN validation test suite finished")