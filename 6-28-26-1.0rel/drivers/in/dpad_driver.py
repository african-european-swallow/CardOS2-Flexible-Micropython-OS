# drivers/in/dpad_driver.py

from core.hardware import hw

class Driver:
    CAPABILITIES = ["dpad"]

    # supports both buses
    I2C_SUPPORT = ["internal"] #"external"

    def __init__(self):
        self.present = False
        self.i2c = None
        self.mcp = None

        self.nav_pins = [0, 1, 3, 2, 4]
        self.names = ["UP", "DOWN", "RIGHT", "LEFT", "CENTER"]

    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
        from mcp23017 import MCP23017

        self.present = False

        preferred = None
        if settings:
            preferred = settings.get("i2c.preferred")

        bus_order = list(self.I2C_SUPPORT)

        if preferred in bus_order:
            bus_order.remove(preferred)
            bus_order.insert(0, preferred)

        for bus_name in bus_order:
            i2c = hw.get_i2c(bus_name)
            if not i2c:
                continue

            try:
                self.mcp = MCP23017(i2c, address=0x20)

                # configure pins as input w/ pullups
                for pin in self.nav_pins:
                    self.mcp.pin(pin, mode=1, pullup=1)

                self.i2c = i2c
                self.present = True
                return

            except Exception as e:
                pass

    # =========================
    # DISCONNECT
    # =========================
    def disconnect(self):
        self.present = False
        self.i2c = None
        self.mcp = None
        
    def probe(self):
        try:
            return (
                self.present and
                self.mcp is not None and
                self.i2c is not None
            )
        except:
            return False
        
    # =========================
    # INPUT
    # =========================
    def get(self, cap):
        if not self.present:
            return []

        if cap == "dpad":
            pressed = []
            for i, pin in enumerate(self.nav_pins):
                if self.mcp.pin(pin) == 0:
                    pressed.append(self.names[i])
            return pressed

        return []