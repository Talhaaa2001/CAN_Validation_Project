import csv
from datetime import datetime

import serial
from serial import SerialException

RECEIVER_PORT = "/dev/cu.usbserial-3"
BAUDRATE = 115200
OUTPUT_FILE = "can_validation_results.csv"


def main():
    try:
        # This script records every line printed by the receiver ESP32.
        ser = serial.Serial(RECEIVER_PORT, BAUDRATE, timeout=1)

        with open(OUTPUT_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "source_port", "raw_line"])

            print("Logging receiver output from", RECEIVER_PORT)
            print("Writing CSV rows to", OUTPUT_FILE)
            print("This script must be the only program reading", RECEIVER_PORT)
            print("Press Ctrl+C to stop.")

            while True:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", "replace").strip()
                timestamp = datetime.now().isoformat(timespec="seconds")
                print(timestamp, "|", line)
                writer.writerow([timestamp, RECEIVER_PORT, line])
                file.flush()
    except SerialException as exc:
        print("Serial port error:", exc)
        print("Close mpremote or any other terminal using", RECEIVER_PORT)
        print("Only one program can read the receiver serial port at a time.")


if __name__ == "__main__":
    main()
