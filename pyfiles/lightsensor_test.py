import smbus
import time

# Sets the default I2C address for the BH1750 light sensor (typically 0x23)
DEVICE = 0x23
# Defines the command byte to put the sensor into a low-power standby mode
POWER_DOWN = 0x00
# Defines the command byte to wake the sensor up and power it on
POWER_ON = 0x01
# Defines the command byte to clear the internal data register of the sensor
RESET = 0x07
# Defines the command for high-resolution mode (1 lux precision) with continuous sampling
CONTINUOUS_HIGH_RES_MODE_1 = 0x10

# Initializes the SMBus object to communicate with I2C devices on Bus 1 of the Pi
bus = smbus.SMBus(1)

# Defines a function to trigger a measurement and calculate the light intensity in Lux
def readLight(addr=DEVICE):
    # Sends the high-resolution mode command to the sensor to start a reading
    bus.write_byte(addr, CONTINUOUS_HIGH_RES_MODE_1)
    # Pauses for 200ms to allow the sensor enough time to integrate the light levels
    time.sleep(0.2)
    # Reads 2 bytes of raw data from the sensor's measurement register via I2C
    data = bus.read_i2c_block_data(addr, CONTINUOUS_HIGH_RES_MODE_1, 2)
    
    # Shifts the first byte 8 bits left, adds the second byte, and divides by 1.2 for Lux
    return ((data[0] << 8) + data[1]) / 1.2

# Enters a try block to handle a graceful exit if the user stops the script
try:
    # Starts an infinite loop to monitor light levels in real-time
    while True:
        # Calls the reading function and stores the calculated Lux value
        lightLevel = readLight()
        # Prints the current light level formatted to two decimal places to the console
        print(f"Light Level: {lightLevel:.2f} lx")
        # Waits for one full second before taking the next measurement
        time.sleep(1)
        
# Catches the signal when the user presses Ctrl+C to terminate the program
except KeyboardInterrupt:
    # Prints a final status message confirming the script has ended safely
    print("Measurement stopped.")
    
