# CAN-Based Embedded Validation Platform using ESP32, MCP2515, OLED, and USB-to-CAN

## Project Goal

This project builds a small automotive-style CAN validation testbed. Two ESP32 boards act like simple ECUs, and each ESP32 talks to an MCP2515 CAN controller over SPI. The MCP2515 modules send CAN frames to each other over CANH/CANL. The sender ECU transmits demo vehicle signals, and the receiver ECU decodes them, validates them, prints PASS/FAIL results, and can show the latest result on an OLED display.

Python scripts on the MacBook can log receiver output, generate CSV/PDF/HTML reports, export frames for SavvyCAN review, and replay captured frames through an SLCAN-compatible USB-to-CAN adapter.

## Hardware Used

- 2x ESP32 boards
- 2x MCP2515 CAN modules with TJA1050 transceivers
- Optional 128x64 SSD1306 I2C OLED display on the receiver ESP32
- Optional SLCAN-compatible USB-to-CAN adapter for SavvyCAN simulation/replay
- MacBook for `mpremote`, serial logging, and CSV reporting

Confirmed ports:

- Sender ECU: `/dev/cu.usbserial-0001`
- Receiver ECU: `/dev/cu.usbserial-3`

## ESP32 to MCP2515 Wiring

Use this wiring on both ESP32/MCP2515 pairs:

| MCP2515 | ESP32 |
| --- | --- |
| VCC | 5V |
| GND | GND |
| CS | GPIO 5 |
| SCK | GPIO 18 |
| SI / MOSI | GPIO 23 |
| SO / MISO | GPIO 19 |
| INT | GPIO 4 |

## Optional Receiver OLED Wiring

The receiver code supports a common SSD1306 I2C OLED. If the OLED is not connected, the receiver still runs normally and prints results over serial.

| OLED | Receiver ESP32 |
| --- | --- |
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

## CAN Bus Wiring

| MCP2515 #1 | MCP2515 #2 |
| --- | --- |
| CANH | CANH |
| CANL | CANL |
| GND | GND, recommended |

Both MCP2515 boards currently have the J1 termination jumper ON.

## Project Structure

```text
CAN_Validation_Project/
├── esp32/
│   ├── mcp2515_test.py        # ESP32 MicroPython SPI test
│   ├── can_loopback_test.py   # ESP32 MicroPython loopback test
│   ├── sender_node.py         # ESP32 sender ECU
│   ├── receiver_node.py       # ESP32 receiver ECU, validator, optional OLED
│   └── ssd1306.py             # MicroPython OLED display driver
├── tools/
│   ├── can_test_suite.py      # Mac Python serial validation runner
│   ├── speed_validator.py     # Mac Python validation rules and thresholds
│   ├── logger.py              # Mac Python raw serial CSV logger
│   ├── generate_can_report.py # Graphical HTML/PDF report generator
│   ├── export_savvycan_csv.py # Export validation CSV to SavvyCAN-friendly CSV
│   ├── slcan_replay_from_csv.py # Replay CSV frames via USB-to-CAN adapter
│   └── check_esp_ports.py     # Mac Python ESP32 port checker
├── diagnostics/
│   ├── mcp2515_status.py      # ESP32 MCP2515 register/status reader
│   └── can_bus_diagnostic.py  # ESP32 listen-only CAN bus diagnostic
├── docs/
│   └── project_evolution.md   # How the project grew over time
├── results/
│   ├── can_validation_results.csv
│   ├── can_validation_results_with_thresholds.csv
│   ├── can_validation_report.html
│   └── can_validation_report.pdf
└── README.md
```

Install Mac Python dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

See `docs/project_evolution.md` for a short explanation of how the project grew from basic MCP2515 testing into OLED display support and SavvyCAN/USB-to-CAN simulation.

## Run Commands

SPI test on sender:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-0001 run esp32/mcp2515_test.py
```

SPI test on receiver:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-3 run esp32/mcp2515_test.py
```

Loopback test on one ESP32/MCP2515 node:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-0001 run esp32/can_loopback_test.py
```

Run the receiver first:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-3 run esp32/receiver_node.py
```

Then run the sender in another terminal:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-0001 run esp32/sender_node.py
```

Important serial-port rule: only one program can read `/dev/cu.usbserial-3` at a time. If `mpremote connect /dev/cu.usbserial-3 run esp32/receiver_node.py` is still open, `python3 tools/logger.py` and `python3 tools/can_test_suite.py` cannot also read that receiver port.

For quick manual testing, use two terminals:

1. Receiver terminal with `mpremote` on `/dev/cu.usbserial-3`
2. Sender terminal with `mpremote` on `/dev/cu.usbserial-0001`

For Mac CSV logging, first copy the receiver code onto the receiver ESP32 as `main.py`, then disconnect `mpremote` so Python can own the serial port:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-3 cp esp32/ssd1306.py :ssd1306.py
~/.local/bin/mpremote connect /dev/cu.usbserial-3 cp esp32/receiver_node.py :main.py
```

After copying, unplug/replug or press reset on the receiver ESP32. Do not keep `mpremote` connected to `/dev/cu.usbserial-3`.

Then run the Mac CSV test suite:

```sh
.venv/bin/python tools/can_test_suite.py
```

Or run the raw serial logger:

```sh
.venv/bin/python tools/logger.py
```

Generate graphical report files from the CSV:

```sh
.venv/bin/python tools/generate_can_report.py
```

This creates `results/can_validation_report.html` and `results/can_validation_results_with_thresholds.csv`. If `matplotlib` is installed, it also creates `results/can_validation_report.pdf`.

Export validation frames for SavvyCAN review:

```sh
.venv/bin/python tools/export_savvycan_csv.py
```

This creates `results/savvycan_frames.csv`.

Replay captured validation frames through an SLCAN-compatible USB-to-CAN adapter:

```sh
.venv/bin/python tools/slcan_replay_from_csv.py --port /dev/cu.YOUR_USB_CAN_PORT --csv results/can_validation_results.csv --bitrate 125000 --delay 0.25
```

Use `.venv/bin/python tools/check_esp_ports.py` and `ls /dev/cu.*` to identify serial ports. Many USB-to-CAN adapters appear as `/dev/cu.usbmodem...` or `/dev/cu.usbserial...`.

Start the sender in another terminal:

```sh
~/.local/bin/mpremote connect /dev/cu.usbserial-0001 run esp32/sender_node.py
```

## Expected Receiver Output

The sender transmits speed values first, so the receiver should begin with lines like:

```text
Received ID: 0x100 | Speed: 40 | Warning: OFF | PASS
Received ID: 0x100 | Speed: 80 | Warning: ON | PASS
Received ID: 0x100 | Speed: 255 | Warning: ON | FAIL
```

After that it also sends RPM, battery voltage, brake status, and coolant temperature demo frames.

If an OLED display is connected to the receiver ESP32, it shows the latest CAN ID, signal value, warning state, and PASS/FAIL result.

If the receiver prints a status line like this:

```text
Ignored non-demo frames: 25 | EFLG: 0x0 | TEC: 0 | REC: 0
```

it means the MCP2515 receive flag was set, but the frame did not match this demo platform's expected one-byte standard IDs. If `REC` is rising or large, such as `REC: 135`, the receiver is seeing CAN receive errors. Recheck that the two modules share GND, CANH goes to CANH, CANL goes to CANL, both nodes use the same bit timing, and both MCP2515 boards use the same crystal frequency. Loopback passing proves SPI and MCP2515 register access, but it does not prove the CANH/CANL physical link.

## CAN Signal Map

These CAN IDs are example mappings for this validation platform. Real vehicle CAN IDs are defined by the OEM or supplier and are normally documented in a DBC file.

| CAN ID | Signal |
| --- | --- |
| `0x100` | Vehicle Speed |
| `0x200` | Engine RPM |
| `0x300` | Battery Voltage |
| `0x400` | Brake Status |
| `0x500` | Coolant Temperature |

## Validation Rules

The receiver checks every CAN message against simple threshold rules. A threshold is the limit where a value changes from valid to invalid, or where a warning turns on.

| Signal | CAN ID | PASS range/value | Warning rule | FAIL condition | Example PASS | Example FAIL |
| --- | --- | --- | --- | --- | --- | --- |
| Vehicle Speed | `0x100` | `0` to `250` | Warning ON if speed is above `50`; Warning OFF if speed is `50` or below | Speed below `0` or above `250`; in this demo `255` is the fault value | `40`, `80` | `255` |
| Engine RPM | `0x200` | `0` to `200` | Not used | RPM above `200` | `120` | `250` |
| Battery Voltage | `0x300` | `10` to `15` | Not used | Voltage below `10` or above `15` | `12` | `9` |
| Brake Status | `0x400` | `0` or `1` only | Not used | Any value other than `0` or `1` | `1` | `3` |
| Coolant Temperature | `0x500` | `70` to `110` | Not used | Temperature below `70` or above `110` | `90` | `130` |

Plain-English meaning:

- Vehicle speed `40` passes because it is inside `0` to `250`, and warning is OFF because it is not above `50`.
- Vehicle speed `80` passes because it is inside `0` to `250`, but warning is ON because it is above `50`.
- Vehicle speed `255` fails because it is above the maximum valid speed of `250`.
- RPM `120` passes, but RPM `250` fails because this demo allows only up to `200`.
- Battery `12` passes, but battery `9` fails because it is below `10`.
- Brake `1` passes because it means pressed; brake `3` fails because only `0` and `1` are allowed.
- Coolant `90` passes, but coolant `130` fails because it is above `110`.

When the Python test suite prints `suite: PASS`, it means the receiver made the correct decision. For example, `receiver: FAIL | expected: FAIL | suite: PASS` is a good result because the injected bad value was correctly detected.

## MCP2515 Register Notes

- `CANCTRL` is the MCP2515 control register. The ESP32 writes this register to request configuration, loopback, or normal mode.
- `CANSTAT` is the MCP2515 status register. It reports the current operating mode.
- `CANINTF` contains interrupt flags. For example, `RX0IF` means a message arrived in receive buffer 0.
- `DLC` means Data Length Code. It tells how many data bytes are in the CAN frame.
- The CAN ID identifies the message type and also participates in bus arbitration.
- Lower CAN IDs have higher priority during arbitration.

Useful mode values:

- `CANCTRL = 0x40` and `CANSTAT = 0x40` means loopback mode.
- `CANCTRL = 0x00` and `CANSTAT = 0x00` means normal mode.
- After reset, `CANSTAT = 0x80` and `CANCTRL` often reads around `0x87`, which means configuration mode.

## Loopback Mode

Loopback mode is a single-node self-test inside the MCP2515. The ESP32 sends a CAN frame into the MCP2515 transmit buffer, and the MCP2515 internally routes that frame back into its receive buffer. This proves the ESP32 SPI connection, MCP2515 register setup, CAN ID packing, DLC, data bytes, and basic transmit/receive logic work.

Loopback mode does not prove the physical CANH/CANL bus or the second MCP2515 module.

## Real Two-Node CAN Communication

Real two-node communication uses both ESP32/MCP2515 nodes. The sender MCP2515 drives the CANH/CANL bus through its TJA1050 transceiver. The receiver MCP2515 reads the physical CAN bus through its own TJA1050 transceiver and passes the decoded frame to the receiver ESP32 over SPI.

This proves the physical CAN wiring, termination, transceivers, normal mode configuration, and ECU-to-ECU communication path.

## SavvyCAN and USB-to-CAN Simulation

SavvyCAN can be used as a CAN bus monitor/simulator with a USB-to-CAN adapter. This project keeps the embedded ESP32/MCP2515 validation path, then adds two Mac-side workflows:

1. Use SavvyCAN to watch the real CAN bus while the ESP32 sender and receiver are running.
2. Use `tools/slcan_replay_from_csv.py` to replay captured validation frames through an SLCAN-compatible USB-to-CAN adapter.

Basic SavvyCAN setup:

- Connect the USB-to-CAN adapter to the same CANH/CANL bus.
- Connect adapter CANH to CANH and CANL to CANL.
- Share GND if the adapter exposes GND.
- Use the same CAN speed: `125000` bit/s.
- In SavvyCAN, open the USB-to-CAN device and select the matching bitrate.

The generated file `results/savvycan_frames.csv` is useful for reviewing the frame set in a table-like format. The replay script sends standard 11-bit CAN frames with one data byte, matching this demo project.

## Validation and Fault Injection

Validation means the receiver checks each decoded CAN signal against an expected rule. If the value is inside the valid range, the result is PASS. If the value is outside the valid range, the result is FAIL.

Fault injection means intentionally sending bad values to prove the validator detects failures. In this project, speed `255`, RPM `250`, battery voltage `9`, brake status `3`, and coolant temperature `130` are example fault-injection values.

## CV Description

Developed a CAN-based embedded validation platform using ESP32, MCP2515 modules, OLED display feedback, SavvyCAN, and a USB-to-CAN adapter. Implemented SPI communication, CAN frame transmission/reception, ECU-to-ECU communication, loopback testing, fault injection, signal validation, OLED status display, CSV/PDF reporting, and USB-to-CAN replay/simulation workflows.

## Updating GitHub

After editing the project, push changes to GitHub with:

```sh
git status
git add .
git commit -m "Update OLED and USB-to-CAN simulation workflow"
git push origin main
```

Check the GitHub repo after pushing:

```text
https://github.com/Talhaaa2001/CAN_Validation_Project
```
