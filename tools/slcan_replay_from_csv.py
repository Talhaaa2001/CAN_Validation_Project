import argparse
import csv
import time

import serial

BITRATE_COMMANDS = {
    10000: "S0",
    20000: "S1",
    50000: "S2",
    100000: "S3",
    125000: "S4",
    250000: "S5",
    500000: "S6",
    800000: "S7",
    1000000: "S8",
}


def make_slcan_frame(can_id, value):
    # SLCAN standard frame format: t + 3 hex ID + 1 hex DLC + data bytes.
    return "t%03X1%02X\r" % (can_id, value & 0xFF)


def read_frames(csv_path):
    with open(csv_path, newline="") as file:
        for row in csv.DictReader(file):
            yield int(row["can_id"], 16), int(row["value"])


def configure_adapter(ser, bitrate):
    speed_command = BITRATE_COMMANDS.get(bitrate)
    if speed_command is None:
        raise ValueError("Unsupported SLCAN bitrate: %s" % bitrate)

    ser.write(b"C\r")  # Close channel if already open.
    time.sleep(0.1)
    ser.write((speed_command + "\r").encode())
    time.sleep(0.1)
    ser.write(b"O\r")  # Open CAN channel.
    time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(
        description="Replay CAN frames from CSV through an SLCAN USB-to-CAN adapter."
    )
    parser.add_argument("--port", required=True, help="USB-CAN serial port")
    parser.add_argument(
        "--csv",
        default="results/can_validation_results.csv",
        help="CSV file containing can_id and value columns",
    )
    parser.add_argument("--bitrate", type=int, default=125000)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    frames = list(read_frames(args.csv))
    if not frames:
        print("No CAN frames found in", args.csv)
        return

    with serial.Serial(args.port, 115200, timeout=1) as ser:
        configure_adapter(ser, args.bitrate)
        print("USB-to-CAN adapter open on", args.port)
        print("Replaying", len(frames), "frames at", args.bitrate, "bit/s")

        try:
            while True:
                for can_id, value in frames:
                    frame = make_slcan_frame(can_id, value)
                    ser.write(frame.encode())
                    print("TX", frame.strip())
                    time.sleep(args.delay)

                if not args.loop:
                    break
        finally:
            ser.write(b"C\r")
            print("CAN channel closed")


if __name__ == "__main__":
    main()
