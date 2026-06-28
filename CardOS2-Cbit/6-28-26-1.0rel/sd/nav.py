from machine import I2C, Pin
from time import sleep
from mcp23017 import MCP23017  

# --- I2C INIT ---
i2c = I2C(0, scl=Pin(4), sda=Pin(3), freq=400000)

# --- MCP INIT ---
mcp = MCP23017(i2c, address=0x20)

# Assign pins for nav switch
UP     = 0
DOWN   = 1
LEFT  = 2
RIGHT   = 3
CENTER = 4

nav_pins = [UP, DOWN, RIGHT, LEFT, CENTER]
names = ["UP", "DOWN", "RIGHT", "LEFT", "CENTER"]

# Configure all nav buttons as input + pull-up
for pin in nav_pins:
    mcp.pin(pin, mode=1, pullup=1)   # 1=input, pullup enabled

print("MCP23017 Navigation Switch Test Running...\n")

# --- Main loop ---
while True:
sssa    for idx, pin in enumerate(nav_pins):
        pressed = (mcp.pin(pin) == 0)  # active-low
        if pressed:
            print(names[idx], "pressed!")
    sleep(0.05)
