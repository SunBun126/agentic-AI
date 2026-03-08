#!/usr/bin/env python3
"""
SCD-30 CO2 Sensor - Raspberry Pi Driver
Library: scd30-i2c  (pip3 install scd30-i2c)
This library is designed for direct Raspberry Pi GPIO I2C — no dongle needed.
"""

import time
import csv
import os
from datetime import datetime
from scd30_i2c import SCD30

# ── Config ────────────────────────────────────────────────────────────────────
MEASUREMENT_INTERVAL_S = 2       # Valid range: 2–1800 seconds
WARMUP_S               = 10      # Stabilisation delay before first read
LOG_TO_CSV             = True
LOG_FILE               = "scd30_log.csv"
CO2_WARN_PPM           = 1000
CO2_ALERT_PPM          = 2000

# ── Helpers ───────────────────────────────────────────────────────────────────
# Defines a function to return a status string based on CO2 concentration levels
def classify_co2(ppm: float) -> str:
    # Checks if the CO2 level is below 600 ppm for an excellent rating
    if ppm < 600:
        # Returns a green checkmark and "Excellent" status
        return "✅ Excellent"
    # Checks if the CO2 level is between 600 and 999 ppm for a good rating
    elif ppm < 1000:
        # Returns a yellow circle and "Good" status
        return "🟡 Good"
    # Checks if the CO2 level is between 1000 and 1999 ppm for a poor rating
    elif ppm < 2000:
        # Returns an orange circle and a suggestion to increase ventilation
        return "🟠 Poor — Increase ventilation"
    # Handles CO2 levels 2000 ppm or higher as a hazardous condition
    else:
        # Returns a red circle and an urgent warning to ventilate immediately
        return "🔴 Hazardous — Ventilate immediately"

# Defines a function to create the CSV log file with headers if it doesn't exist
def init_csv(path: str): 
    # Checks the file system to see if the specified log file path already exists
    if not os.path.exists(path): 
        # Opens a new file in write mode ensuring correct newline handling for CSVs
        with open(path, "w", newline="") as f: 
            # Writes the column headers as the first row of the CSV file
            csv.writer(f).writerow(["timestamp", "co2_ppm", "temperature_c", "humidity_rh"])
        # Prints a confirmation message to the console that a new file was created
        print(f"[LOG] Created: {path}")

# Defines a function to append a new row of sensor data to the CSV file
def append_csv(path: str, co2: float, temp: float, hum: float):
    # Opens the existing log file in append mode to add data without overwriting
    with open(path, "a", newline="") as f:
        # Writes the current time and sensor readings formatted to specific decimals
        csv.writer(f).writerow([
            # Records the current date and time in ISO 8601 string format
            datetime.now().isoformat(),
            # Formats CO2 as an integer and floats to two decimal places
            f"{co2:.0f}", f"{temp:.2f}", f"{hum:.2f}"
        ])

# Defines a function to manually calibrate the sensor against a known air quality
def forced_recalibration(scd30: SCD30, reference_ppm: int = 400):
    # Docstring explaining that the sensor needs outdoor air for this process
    """Run in fresh outdoor air (~400 ppm). Uncomment call in main() to use."""
    # Informs the user that the calibration process has started and requires time
    print("[CAL] Exposing sensor to reference air for 2 minutes...")
    # Pauses execution for 120 seconds to allow the sensor to stabilize in fresh air
    time.sleep(120)
    # Sends the command to the SCD30 to set the current air as the reference level
    scd30.forced_recalibration_with_reference(reference_ppm)
    # Prints a message confirming the calibration has been successfully completed
    print(f"[CAL] Done — reference set to {reference_ppm} ppm")

# ── Main ──────────────────────────────────────────────────────────────────────
# Defines the primary execution block for the script
def main():
    # Prints a visual separator line for the console UI
    print("=" * 50)
    # Prints the title header of the application
    print("  SCD-30 CO2 Sensor — Raspberry Pi")
    # Prints a closing separator line for the UI header
    print("=" * 50)

    # Checks the config flag to determine if CSV logging should be initialized
    if LOG_TO_CSV:
        # Calls the helper function to prepare the CSV file
        init_csv(LOG_FILE)

    # Initializes the SCD30 object to establish communication via I2C
    scd30 = SCD30()
    # Configures the sensor's internal clock for how often it takes a reading
    scd30.set_measurement_interval(MEASUREMENT_INTERVAL_S)
    # Commands the sensor to begin its continuous measurement mode
    scd30.start_periodic_measurement()

    # Displays a message indicating the sensor's mandatory warmup period
    print(f"[INFO] Warming up for {WARMUP_S}s — please wait...")
    # Pauses the script for the duration of the defined warmup period
    time.sleep(WARMUP_S)
    # Notifies the user that monitoring has begun and how to exit
    print("[INFO] Ready. Press Ctrl+C to stop.\n")

    # Placeholder for the calibration function, commented out by default
    # forced_recalibration(scd30, reference_ppm=400)

    # Enters a try block to gracefully handle user interruption (Ctrl+C)
    try:
        # Starts an infinite loop to continuously poll the sensor for data
        while True:
            # Asks the sensor if a new measurement is ready to be read
            if scd30.get_data_ready():
                # Retrieves the actual CO2, temperature, and humidity values
                measurement = scd30.read_measurement()

                # Checks if the measurement returned valid data rather than empty
                if measurement is not None:
                    # Unpacks the measurement tuple into individual variables
                    co2, temperature, humidity = measurement
                    # Captures the current time in a human-readable format for display
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Prints the timestamp for the current data point
                    print(f"[{ts}]")
                    # Displays the CO2 level and its classification (e.g., "Good")
                    print(f"  CO2         : {co2:.0f} ppm  — {classify_co2(co2)}")
                    # Displays the temperature reading in Celsius
                    print(f"  Temperature : {temperature:.2f} °C")
                    # Displays the relative humidity percentage
                    print(f"  Humidity    : {humidity:.2f} % RH")
                    # Prints a separator line to distinguish between readings
                    print("-" * 50)

                    # Checks if the CO2 level has reached the critical Alert threshold
                    if co2 >= CO2_ALERT_PPM:
                        # Prints a high-priority alert message to the console
                        print(f"  ‼ ALERT: CO2 above {CO2_ALERT_PPM} ppm!")
                    # Checks if the CO2 level has reached the Warning threshold
                    elif co2 >= CO2_WARN_PPM:
                        # Prints a standard warning message to the console
                        print(f"  ⚠ WARNING: CO2 above {CO2_WARN_PPM} ppm")

                    # Checks the config flag to determine if data should be saved
                    if LOG_TO_CSV:
                        # Appends the latest readings to the specified CSV file
                        append_csv(LOG_FILE, co2, temperature, humidity)
                # Handles the case where the sensor failed to provide data
                else:
                    # Prints a warning that no data was received during this poll
                    print("[WARN] Measurement returned None — retrying...")
            # If data is not ready yet, informs the user it is still waiting
            else:
                # Prints a status message indicating the sensor is still processing
                print("[INFO] Waiting for data ready...")

            # Wait for the specified interval before the next loop iteration
            time.sleep(MEASUREMENT_INTERVAL_S)

    # Catches the signal when the user presses Ctrl+C
    except KeyboardInterrupt:
        # Prints a status message that the shutdown process has started
        print("\n[INFO] Stopping...")
        # Sends a command to the SCD30 to stop taking measurements to save power
        scd30.stop_periodic_measurement()
        # Confirms to the user that the sensor is now inactive
        print("[INFO] Sensor stopped.")

# Standard Python idiom to ensure main() only runs if the script is executed directly
if __name__ == "__main__":
    # Executes the main function
    main()
