import csv
import os

INPUT_FILE = "results/can_validation_results.csv"
OUTPUT_FILE = "results/savvycan_frames.csv"


def main():
    os.makedirs("results", exist_ok=True)

    with open(INPUT_FILE, newline="") as input_file:
        rows = list(csv.DictReader(input_file))

    with open(OUTPUT_FILE, "w", newline="") as output_file:
        fieldnames = [
            "timestamp",
            "bus",
            "id",
            "extended",
            "dlc",
            "data",
            "signal",
            "value",
            "receiver_result",
            "suite_result",
        ]
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            value = int(row["value"]) & 0xFF
            writer.writerow(
                {
                    "timestamp": row["timestamp"],
                    "bus": 0,
                    "id": row["can_id"],
                    "extended": 0,
                    "dlc": 1,
                    "data": "%02X" % value,
                    "signal": row["signal"],
                    "value": row["value"],
                    "receiver_result": row["receiver_result"],
                    "suite_result": row["suite_result"],
                }
            )

    print("Wrote", OUTPUT_FILE)


if __name__ == "__main__":
    main()
