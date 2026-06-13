from datetime import datetime

CAN_ID_SPEED = 0x100
CAN_ID_RPM = 0x200
CAN_ID_BATTERY = 0x300
CAN_ID_BRAKE = 0x400
CAN_ID_COOLANT = 0x500

SIGNAL_NAMES = {
    CAN_ID_SPEED: "Vehicle Speed",
    CAN_ID_RPM: "Engine RPM",
    CAN_ID_BATTERY: "Battery Voltage",
    CAN_ID_BRAKE: "Brake Status",
    CAN_ID_COOLANT: "Coolant Temperature",
}

SIGNAL_THRESHOLDS = {
    CAN_ID_SPEED: {
        "pass_rule": "0 <= speed <= 250",
        "warning_rule": "Warning ON if speed > 50",
        "fail_rule": "speed < 0 or speed > 250",
        "example_pass": "40, 80",
        "example_fail": "255",
    },
    CAN_ID_RPM: {
        "pass_rule": "0 <= rpm <= 200",
        "warning_rule": "N/A",
        "fail_rule": "rpm > 200",
        "example_pass": "120",
        "example_fail": "250",
    },
    CAN_ID_BATTERY: {
        "pass_rule": "10 <= voltage <= 15",
        "warning_rule": "N/A",
        "fail_rule": "voltage < 10 or voltage > 15",
        "example_pass": "12",
        "example_fail": "9",
    },
    CAN_ID_BRAKE: {
        "pass_rule": "brake is 0 or 1",
        "warning_rule": "N/A",
        "fail_rule": "brake is not 0 or 1",
        "example_pass": "1",
        "example_fail": "3",
    },
    CAN_ID_COOLANT: {
        "pass_rule": "70 <= temp <= 110",
        "warning_rule": "N/A",
        "fail_rule": "temp < 70 or temp > 110",
        "example_pass": "90",
        "example_fail": "130",
    },
}


def get_threshold(can_id):
    return SIGNAL_THRESHOLDS.get(
        can_id,
        {
            "pass_rule": "unknown",
            "warning_rule": "unknown",
            "fail_rule": "unknown CAN ID",
            "example_pass": "N/A",
            "example_fail": "N/A",
        },
    )


def validate_signal(can_id, value):
    """Return signal name, warning state, PASS/FAIL result, and reason."""
    if can_id == CAN_ID_SPEED:
        warning = "ON" if value > 50 else "OFF"
        if 0 <= value <= 250:
            return SIGNAL_NAMES[can_id], warning, "PASS", "speed in valid range"
        return SIGNAL_NAMES[can_id], warning, "FAIL", "speed fault"

    if can_id == CAN_ID_RPM:
        if 0 <= value <= 200:
            return SIGNAL_NAMES[can_id], "N/A", "PASS", "rpm in valid range"
        return SIGNAL_NAMES[can_id], "N/A", "FAIL", "rpm fault"

    if can_id == CAN_ID_BATTERY:
        if 10 <= value <= 15:
            return SIGNAL_NAMES[can_id], "N/A", "PASS", "voltage in valid range"
        return SIGNAL_NAMES[can_id], "N/A", "FAIL", "voltage fault"

    if can_id == CAN_ID_BRAKE:
        if value == 0 or value == 1:
            return SIGNAL_NAMES[can_id], "N/A", "PASS", "brake status valid"
        return SIGNAL_NAMES[can_id], "N/A", "FAIL", "brake status fault"

    if can_id == CAN_ID_COOLANT:
        if 70 <= value <= 110:
            return SIGNAL_NAMES[can_id], "N/A", "PASS", "coolant temperature valid"
        return SIGNAL_NAMES[can_id], "N/A", "FAIL", "coolant temperature fault"

    return "Unknown", "N/A", "FAIL", "unknown CAN ID"


def print_result(can_id, value):
    signal, warning, result, reason = validate_signal(can_id, value)
    print(
        f"{datetime.now()} | ID={hex(can_id)} | {signal}={value} | "
        f"Warning={warning} | {result} | {reason}"
    )


if __name__ == "__main__":
    # Small desktop sanity check for the validation rules.
    sample_frames = [
        (CAN_ID_SPEED, 40),
        (CAN_ID_SPEED, 80),
        (CAN_ID_SPEED, 255),
        (CAN_ID_RPM, 120),
        (CAN_ID_RPM, 250),
        (CAN_ID_BATTERY, 12),
        (CAN_ID_BATTERY, 9),
        (CAN_ID_BRAKE, 1),
        (CAN_ID_BRAKE, 3),
        (CAN_ID_COOLANT, 90),
        (CAN_ID_COOLANT, 130),
    ]

    for sample_can_id, sample_value in sample_frames:
        print_result(sample_can_id, sample_value)
