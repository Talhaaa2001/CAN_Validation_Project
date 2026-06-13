import csv
from datetime import datetime

import serial
from serial import SerialException

from speed_validator import get_threshold, validate_signal

RECEIVER_PORT = "/dev/cu.usbserial-3"
BAUDRATE = 115200
OUTPUT_FILE = "can_validation_results.csv"
MAX_FRAMES = 30


def parse_receiver_line(line):
    # Expected examples:
    # Received ID: 0x100 | Speed: 40 | Warning: OFF | PASS
    # Received ID: 0x200 | RPM: 120 | PASS
    if not line.startswith("Received ID:"):
        return None

    parts = [part.strip() for part in line.split("|")]
    can_id = int(parts[0].split(":", 1)[1].strip(), 16)
    signal_name, value_text = parts[1].split(":", 1)
    value = int(value_text.strip())

    receiver_warning = "N/A"
    receiver_result = parts[-1].strip()

    if len(parts) == 4 and parts[2].startswith("Warning:"):
        receiver_warning = parts[2].split(":", 1)[1].strip()

    return can_id, signal_name.strip(), value, receiver_warning, receiver_result


def main():
    try:
        ser = serial.Serial(RECEIVER_PORT, BAUDRATE, timeout=1)

        with open(OUTPUT_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "timestamp",
                    "can_id",
                    "signal",
                    "value",
                    "receiver_warning",
                    "expected_warning",
                    "receiver_result",
                    "expected_result",
                    "suite_result",
                    "reason",
                    "pass_rule",
                    "warning_rule",
                    "fail_rule",
                    "example_pass",
                    "example_fail",
                ]
            )

            print("CAN test suite listening on", RECEIVER_PORT)
            print("Writing report to", OUTPUT_FILE)
            print("This script must be the only program reading", RECEIVER_PORT)
            print("If mpremote is attached to the receiver, stop it first.")

            frames_seen = 0
            while frames_seen < MAX_FRAMES:
                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", "replace").strip()
                parsed = parse_receiver_line(line)
                if parsed is None:
                    print(line)
                    continue

                can_id, signal, value, receiver_warning, receiver_result = parsed
                expected_signal, expected_warning, expected_result, reason = (
                    validate_signal(can_id, value)
                )
                threshold = get_threshold(can_id)

                warning_matches = (
                    receiver_warning == expected_warning or expected_warning == "N/A"
                )
                result_matches = receiver_result == expected_result
                suite_result = "PASS" if warning_matches and result_matches else "FAIL"
                timestamp = datetime.now().isoformat(timespec="seconds")

                print(
                    timestamp,
                    "|",
                    hex(can_id),
                    "|",
                    signal,
                    value,
                    "| receiver:",
                    receiver_result,
                    "| expected:",
                    expected_result,
                    "| suite:",
                    suite_result,
                )

                writer.writerow(
                    [
                        timestamp,
                        hex(can_id),
                        expected_signal,
                        value,
                        receiver_warning,
                        expected_warning,
                        receiver_result,
                        expected_result,
                        suite_result,
                        reason,
                        threshold["pass_rule"],
                        threshold["warning_rule"],
                        threshold["fail_rule"],
                        threshold["example_pass"],
                        threshold["example_fail"],
                    ]
                )
                file.flush()
                frames_seen += 1

            print("CAN test suite finished after", frames_seen, "frames")
    except SerialException as exc:
        print("Serial port error:", exc)
        print("Close mpremote or any other terminal using", RECEIVER_PORT)
        print("Only one program can read the receiver serial port at a time.")


if __name__ == "__main__":
    main()
