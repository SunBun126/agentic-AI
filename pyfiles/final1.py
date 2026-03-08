import time
import board
import smbus2 as smbus
import neopixel
from gpiozero import OutputDevice
from scd30_i2c import SCD30
import adafruit_bme280.basic as adafruit_bme280


from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 1. Hardware Setup 
# Initializes the relay or MOSFET control for the water pump on GPIO pin 17
pump = OutputDevice(17)

# Lights
# Specifies that the NeoPixel data line is connected to GPIO pin 10
PIXEL_PIN = board.D10
# Defines the total number of individual LEDs in the NeoPixel strip
NUM_PIXELS = 20
# Sets the color sequence to Green-Red-Blue, standard for most WS2812B strips
ORDER = neopixel.GRB
# Configures the NeoPixel object with specific pin, count, brightness, and manual update mode
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.2, auto_write=False, pixel_order=ORDER)

# BME280 (Temp, Humidity, Pressure)
# Sets up the I2C communication bus for the Raspberry Pi
i2c = board.I2C()
# Initializes the BME280 sensor using the I2C bus at the specific address 0x76
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

# SCD30 (CO2)
# Creates an instance of the SCD30 CO2 sensor driver
scd30 = SCD30()
# Sets the sensor to take a new CO2 measurement every 2 seconds
scd30.set_measurement_interval(2)
# Commands the SCD30 to start the continuous measurement cycle
scd30.start_periodic_measurement()

# Light Sensor (BH1750)
# Opens the SMBus interface for I2C communication (Channel 1)
bus = smbus.SMBus(1)
# Sets the default I2C address for the BH1750 light sensor
DEVICE = 0x23
# Defines the command byte to start high-resolution continuous measurement mode
CONTINUOUS_HIGH_RES_MODE_1 = 0x10


# 2. Creating AI Tools using @tool syntax
# Decorator that converts the following function into a LangChain-compatible tool
@tool
def take_sensor_reading() -> str:
    """Take a sensor reading for temperature, humidity, CO2, and light."""
    # Pulls the current temperature value from the BME280 sensor
    temperature = bme280.temperature
    # Pulls the current relative humidity percentage from the BME280 sensor
    humidity = bme280.humidity
    
    # Initializes a default CO2 value of 0 in case the sensor isn't ready
    co2 = 0
    # Queries the SCD30 to see if a fresh measurement is available in its buffer
    if scd30.get_data_ready():
        # Reads the tuple containing CO2, Temperature, and Humidity from the SCD30
        measurement = scd30.read_measurement()
        # Checks if the measurement returned data successfully
        if measurement is not None:
            # Extracts the CO2 concentration (the first element in the tuple)
            co2 = measurement[0]
            
    # Read Light Sensor
    # Sends a command to the BH1750 to trigger a high-resolution reading
    bus.write_byte(DEVICE, CONTINUOUS_HIGH_RES_MODE_1)
    # Pauses for 200ms to allow the sensor to complete the light integration
    time.sleep(0.2)
    # Reads 2 bytes of data from the sensor's measurement register
    data = bus.read_i2c_block_data(DEVICE, CONTINUOUS_HIGH_RES_MODE_1, 2)
    # Combines the high and low bytes and divides by 1.2 to calculate Lux
    light = ((data[0] << 8) + data[1]) / 1.2
    
    # Formats all gathered sensor data into a single descriptive string
    reading_result = f"Temp: {temperature:.1f}C, Hum: {humidity:.1f}%, CO2: {co2:.0f}ppm, Light: {light:.1f}lx"
    # Prints the data string to the local console for debugging
    print(f"Sensor reading: {reading_result}")
    # Returns the formatted string so the AI model can process the numbers
    return reading_result

# Decorator that registers the pump function as an AI-callable tool
@tool
def turn_on_pump() -> str:
    """Turn on the pump for 3 seconds to water the plants."""
    # Prints a status message to indicate the physical action starting
    print("\nAction: Turning on pump")
    # Sends the GPIO signal to activate the pump (starts watering)
    pump.on()
    # Keeps the pump running for 3 seconds to deliver a set amount of water
    time.sleep(3)
    # Sends the GPIO signal to deactivate the pump (stops watering)
    pump.off()
    # Returns a confirmation message to the AI
    return "Pump watered the plants"

# Decorator that registers the lighting function as an AI-callable tool
@tool
def turn_on_lights(color_name: str) -> str:
    """Turn on the grow lights. color_name can be 'red', 'green', 'blue', or 'off'."""
    # Prints the chosen color action to the console
    print(f"\nAction: Changing lights to {color_name}")
    
    # Checks if the AI requested the color red
    if color_name.lower() == 'red':
        # Sets the RGB tuple to full red intensity
        color = (255, 0, 0)
    # Checks if the AI requested the color green
    elif color_name.lower() == 'green':
        # Sets the RGB tuple to full green intensity
        color = (0, 255, 0)
    # Checks if the AI requested the color blue
    elif color_name.lower() == 'blue':
        # Sets the RGB tuple to full blue intensity
        color = (0, 0, 255)
    # Handles "off" or any unrecognized color
    else:
        # Sets the RGB tuple to black (LEDs off)
        color = (0, 0, 0) # Off
        

    # Iterates through every LED in the strip to apply the color
    for i in range(NUM_PIXELS):
        # Assigns the color to the specific LED at index i
        pixels[i] = color
        # Pushes the updated data to the physical LED strip
        pixels.show()
        # Adds a short delay to create a "filling" animation effect
        time.sleep(0.05)
        
    # Returns a status update to the AI model
    return f"Lights are now {color_name}"


# Initializes the connection to the Large Language Model via OpenRouter
model = ChatOpenAI(
    # Sets the unique authentication key for the API
    api_key="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",
    # Defines the URL endpoint for OpenRouter's service
    base_url="https://openrouter.ai/api/v1",
    # Specifies the specific AI model (Qwen 3) to use for decision making
    model="qwen/qwen3-235b-a22b",
    # Sets randomness to 0.2 to keep the AI focused and logical
    temperature=0.2,
)

# Lists the available tools for the AI to interact with the hardware
tools = [take_sensor_reading, turn_on_pump, turn_on_lights]

# Creates the agent logic that connects the model to the tools and instructions
agent = create_agent(
    # Attaches the tools to the model and prevents it from trying to do two things at once
    model.bind_tools(tools, parallel_tool_calls=False),
    # Passes the list of functions the agent is allowed to execute
    tools,
    # Defines the core persona and the strict logic rules the AI must follow
    system_prompt="""You are an environment controller. Follow these rules strictly:
1. Always call take_sensor_reading first.
2. If humidity < 50: call turn_on_pump.
3. If light < 100: call turn_on_lights with 'red' or 'blue'.
4. If light >= 100: call turn_on_lights with 'off'.
5. when in doubt, do the first thing that comes to mind, don't overthink it.
"""
)


# 4. Continuous Running Loop
# Waits 2 seconds to ensure all I2C sensors have finished their internal boot-up
time.sleep(2) # Give sensors a brief moment to warm up

# Starts a persistent loop to manage the environment indefinitely
try:
    # Runs the logic inside the loop forever
    while True:
        # Commands the AI agent to check sensors and perform actions based on the prompt
        agent.invoke({"messages": [{"role": "user", "content": "Check the sensor first, then act."}]})
        # Pauses the script for one minute before the next environment check
        time.sleep(60) # Wait 60 seconds before next check
        
# Catches the signal when the user stops the script (Ctrl+C)
except KeyboardInterrupt:
    # Informs the user that the program is shutting down safely
    print("\nStopping...")
    # Ensures the water pump is physically turned off to prevent flooding
    pump.off()
    # Sets all LED colors to black (off)
    pixels.fill((0, 0, 0))
    # Updates the LED strip to apply the "off" state
    pixels.show()
    # Commands the CO2 sensor to stop measuring to extend its lifespan
    scd30.stop_periodic_measurement()



