#!/usr/bin/env python3
"""
BME280 Pressure + Temperature + Humidity — Raspberry Pi
Install: pip3 install adafruit-blinka adafruit-circuitpython-bme280
I2C Address: 0x76 (detected via i2cdetect)
Chip ID 0x60 = BME280 (includes humidity — better than BMP280)
"""

import time
import csv
import os
from datetime import datetime

import board
import adafruit_bme280.basic as adafruit_bme280  # ✅ Changed from adafruit_bmp280

# ── Config ────────────────────────────────────────────────────────────────────
I2C_ADDRESS        = 0x76    # Confirmed from i2cdetect
SEA_LEVEL_PRESSURE = 1013.25 # hPa — adjust for local sea level
POLL_INTERVAL_S    = 2
LOG_TO_CSV         = True
LOG_FILE           = "bme280_log.csv"

TEMP_WARN_HIGH     = 35.0    # °C
PRESSURE_WARN_LOW  = 980.0   # hPa

# ── Helpers ───────────────────────────────────────────────────────────────────
# Defines a function to categorize barometric pressure into weather-related status strings
def classify_pressure(hpa: float) -> str:
    # Checks if the pressure is 1013 hPa or higher, indicating a high-pressure system
    if hpa >= 1013:
        # Returns a blue circle and a "fair weather" description
        return "🔵 High pressure (fair weather)"
    # Checks if the pressure is between 990 and 1012 hPa
    elif hpa >= 990:
        # Returns a yellow circle and a "Normal" status label
        return "🟡 Normal"
    # Handles any pressure readings below 990 hPa
    else:
        # Returns an orange circle and warns of potential incoming rain
        return "🟠 Low pressure (possible rain)"

# Defines a function to categorize relative humidity percentages for human comfort
def classify_humidity(rh: float) -> str:
    # Checks if the relative humidity is lower than 30%
    if rh < 30:
        # Returns an orange circle and a "Dry" air quality label
        return "🟠 Dry"
    # Checks if the relative humidity is between 30% and 59%
    elif rh < 60:
        # Returns a green checkmark and a "Comfortable" air quality label
        return "✅ Comfortable"
    # Handles any humidity readings 60% or higher
    else:
        # Returns a yellow circle and a "Humid" air quality label
        return "🟡 Humid"

# Defines a function to create a new CSV log file and write the header row
def init_csv(path: str):
    # Verifies if the file already exists to avoid overwriting existing data
    if not os.path.exists(path):
        # Opens the file in write mode with proper newline handling for CSV standards
        with open(path, "w", newline="") as f:
            # Writes the specific column names for timestamp and all BME280 metrics
            csv.writer(f).writerow([
                "timestamp", "temperature_c", "humidity_rh",
                "pressure_hpa", "altitude_m"
            ])
        # Prints a status message confirming the log file creation
        print(f"[LOG] Created: {path}")

# Defines a function to add a new row of sensor data to the end of the CSV file
def append_csv(path: str, temp: float, humidity: float,
               pressure: float, altitude: float):
    # Opens the log file in append mode to keep previous entries intact
    with open(path, "a", newline="") as f:
        # Writes a list of current values formatted as strings to the CSV
        csv.writer(f).writerow([
            # Records the current date and time in a standard ISO string format
            datetime.now().isoformat(),
            # Formats the temperature, humidity, pressure, and altitude to two decimal places
            f"{temp:.2f}", f"{humidity:.2f}",
            f"{pressure:.2f}", f"{altitude:.2f}"
        ])

# ── Main ──────────────────────────────────────────────────────────────────────
# Defines the entry point for the sensor monitoring script
def main():
    # Prints a visual border for the console output header
    print("=" * 50)
    # Prints the main title of the script for the user
    print("  BME280 Pressure + Temp + Humidity — Raspberry Pi")
    # Prints the closing border for the console output header
    print("=" * 50)

    # Checks the configuration flag to see if file logging is enabled
    if LOG_TO_CSV:
        # Runs the initialization function for the log file
        init_csv(LOG_FILE)

    # Sets up the shared I2C bus for hardware communication
    i2c   = board.I2C()
    # Initializes the physical BME280 sensor at the specified I2C address
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=I2C_ADDRESS)  # ✅ Changed
    # Calibrates the sensor by providing the current local sea-level pressure
    bme280.sea_level_pressure = SEA_LEVEL_PRESSURE

    # Displays the active I2C address in hexadecimal format for verification
    print(f"[INFO] BME280 ready at I2C address 0x{I2C_ADDRESS:02X}")
    # Displays the reference pressure being used for altitude calculations
    print(f"[INFO] Sea-level pressure reference: {SEA_LEVEL_PRESSURE} hPa")
    # Tells the user how to safely stop the script
    print("[INFO] Press Ctrl+C to stop.\n")

    # Starts a try block to catch the KeyboardInterrupt signal
    try:
        # Enters a loop to continuously poll the sensor
        while True:
            # Reads the current temperature from the sensor in Celsius
            temperature = bme280.temperature   # °C
            # Reads the current relative humidity percentage from the sensor
            humidity    = bme280.humidity      # % RH  ✅ New — BME280 only
            # Reads the current barometric pressure in hectopascals
            pressure    = bme280.pressure      # hPa
            # Calculates the estimated altitude based on the current pressure
            altitude    = bme280.altitude      # metres
            # Generates a human-readable timestamp for the console output
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Prints the time of the current reading
            print(f"[{ts}]")
            # Displays the temperature formatted to two decimal places
            print(f"  Temperature : {temperature:.2f} °C")
            # Displays humidity and its comfort classification
            print(f"  Humidity    : {humidity:.2f} % RH  — {classify_humidity(humidity)}")
            # Displays barometric pressure and its weather classification
            print(f"  Pressure    : {pressure:.2f} hPa   — {classify_pressure(pressure)}")
            # Displays the calculated altitude in meters
            print(f"  Altitude    : {altitude:.2f} m")
            # Prints a separator line for clarity between readings
            print("-" * 50)

            # Checks if the temperature has exceeded the user-defined high limit
            if temperature >= TEMP_WARN_HIGH:
                # Prints a high-temperature warning to the console
                print(f"  ⚠ WARNING: Temperature above {TEMP_WARN_HIGH}°C!")
            # Checks if the pressure has dropped below the user-defined low limit
            if pressure <= PRESSURE_WARN_LOW:
                # Prints a low-pressure warning (storm warning) to the console
                print(f"  ⚠ WARNING: Pressure below {PRESSURE_WARN_LOW} hPa!")

            # Checks the flag to determine if data should be written to disk
            if LOG_TO_CSV:
                # Appends the current sensor values to the log file
                append_csv(LOG_FILE, temperature, humidity, pressure, altitude)

            # Pauses the script for the duration of the polling interval
            time.sleep(POLL_INTERVAL_S)

    # Executes if the user presses Ctrl+C
    except KeyboardInterrupt:
        # Prints a simple message to confirm the script has stopped
        print("\n[INFO] Stopped.")

# Conditional check to ensure the main function only runs when the file is executed
if __name__ == "__main__":
    # Calls the main entry point function
    main()


 
