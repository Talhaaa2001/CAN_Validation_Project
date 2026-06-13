import glob

EXPECTED_PORTS = {
    "/dev/cu.usbserial-0001": "Sender ECU",
    "/dev/cu.usbserial-3": "Receiver ECU",
}


def main():
    ports = sorted(glob.glob("/dev/cu.usbserial*"))

    if not ports:
        print("No ESP32 USB serial ports found.")
        return

    print("Detected ESP32 USB serial ports:")

    for port in ports:
        role = EXPECTED_PORTS.get(port, "Unknown ESP32")
        print(f"{role}: {port}")

    missing = [role for port, role in EXPECTED_PORTS.items() if port not in ports]

    if missing:
        print("Missing expected board(s):", ", ".join(missing))


if __name__ == "__main__":
    main()
