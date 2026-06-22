# Project Evolution

This project was developed in stages. The file and folder names in the current repository use the final organized structure, while the project history explains how the scope grew.

## Stage 1: Basic CAN Bring-Up

The first version focused on proving the ESP32 could communicate with the MCP2515 over SPI.

- `esp32/mcp2515_test.py` checked MCP2515 register access.
- `esp32/can_loopback_test.py` proved CAN frame packing and receive logic inside one MCP2515.

## Stage 2: Two-Node CAN Validation

The second version used two ESP32 boards and two MCP2515 modules as sender and receiver ECUs.

- `esp32/sender_node.py` transmits demo vehicle signals.
- `esp32/receiver_node.py` receives, decodes, validates, and prints PASS/FAIL results.
- `tools/can_test_suite.py` logs receiver output and creates validation CSV data.

## Stage 3: Reporting and Threshold Tables

The Mac-side tooling was extended to create readable validation artifacts.

- `results/can_validation_results.csv` stores captured test results.
- `results/can_validation_results_with_thresholds.csv` adds PASS/FAIL threshold rules.
- `results/can_validation_report.html` and `results/can_validation_report.pdf` provide graphical reports.

## Stage 4: OLED Display

The receiver was updated to support a small SSD1306 OLED display. This gives immediate embedded feedback without needing to watch the serial terminal.

- `esp32/ssd1306.py` is the MicroPython OLED driver.
- `esp32/receiver_node.py` shows the latest CAN ID, signal value, warning state, and PASS/FAIL result when an OLED is connected.

## Stage 5: SavvyCAN and USB-to-CAN Simulation

The project was extended so the same CAN validation data can be reviewed or replayed with external CAN tooling.

- `tools/export_savvycan_csv.py` exports validation frames for SavvyCAN-style review.
- `tools/slcan_replay_from_csv.py` replays captured frames through an SLCAN-compatible USB-to-CAN adapter.
- `results/savvycan_frames.csv` contains the exported CAN frame set.

## Naming Decision

The current file names are intentionally simple and descriptive:

- `sender_node.py` and `receiver_node.py` describe the ESP32 ECU roles.
- `can_test_suite.py` describes the Mac-side validation runner.
- `export_savvycan_csv.py` and `slcan_replay_from_csv.py` describe the USB-to-CAN/SavvyCAN workflow.
- `project_evolution.md` documents that the project grew over time instead of renaming every file after each new feature.

This is normal in engineering projects: names can stay stable while README documentation explains new features added later.
