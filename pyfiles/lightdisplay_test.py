import board
import neopixel
import time
 
# Configuration
# ON PI 5: Use board.SPI() or specify Pin 10 if using SPI method
# If standard GPIO 18 doesn't work, we use the SPI port (GPIO 10)
PIXEL_PIN = board.D10  
NUM_PIXELS = 20  # Change this to match your number of LEDs
ORDER = neopixel.GRB  # WS2812B is usually GRB, not RGB
 
# Initializes the NeoPixel LED strip object with specific hardware parameters
pixels = neopixel.NeoPixel(
    # Sets the GPIO pin on the Raspberry Pi where the data wire is connected
    PIXEL_PIN, 
    # Sets the total count of LEDs in the connected strip or ring
    NUM_PI_XELS, 
    # Sets the global brightness level between 0.0 (off) and 1.0 (full)
    brightness=0.2, 
    # Disables automatic updates so changes only happen when .show() is called
    auto_write=False,
    # Defines the specific color wire order (e.g., GRB or RGB) for the LEDs
    pixel_order=ORDER
)
 
# Defines a function to create a "filling" animation by lighting LEDs one by one
def color_wipe(color, wait):
    # Docstring describing that the function creates a sequential color wipe effect
    """Wipe color across display a pixel at a time."""
    # Starts a loop that iterates through every individual LED index
    for i in range(NUM_PIXELS):
        # Assigns the target RGB color to the specific LED at the current index
        pixels[i] = color
        # Pushes the data to the physical LEDs to make the change visible
        pixels.show()
        # Pauses for a short duration to control the speed of the wipe animation
        time.sleep(wait)
 
# Begins a block to monitor for user interruption (like Ctrl+C)
try:
    # Starts an infinite loop to keep the light show running continuously
    while True:
        # Prints the current color being displayed to the console
        print("Red")
        # Calls the wipe function with a full Red tuple and a 50ms delay
        color_wipe((255, 0, 0), 0.05)  # Red
 
        # Prints the next color phase to the console
        print("Green")
        # Calls the wipe function with a full Green tuple and a 50ms delay
        color_wipe((0, 255, 0), 0.05)  # Green
 
        # Prints the next color phase to the console
        print("Blue")
        # Calls the wipe function with a full Blue tuple and a 50ms delay
        color_wipe((0, 0, 0), 0.05)  # Blue
 
        # Prints a status message indicating the lights are being turned off
        print("Off")
        # Calls the wipe function with black (0,0,0) and a faster 10ms delay
        color_wipe((0, 0, 0), 0.01)    # Off
        # Pauses for one full second before restarting the entire color sequence
        time.sleep(1)
 
# Catches the signal when the user stops the script manually
except KeyboardInterrupt:
    # Prints a final message to the console as the program exits
    print("\nStopping...")
    # Commands every LED in the memory buffer to turn off (Black)
    pixels.fill((0, 0, 0))
    # Pushes the "all off" command to the physical LED hardware
    pixels.show()
