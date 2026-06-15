from machine import Pin, SoftI2C

class Hardware:
    def __init__(self, settings=None):
        self.settings = settings
        self.i2c_buses = {}

        self._init_i2c()

    # =========================
    # INIT I2C FROM SETTINGS
    # =========================
    def _init_i2c(self):
        s = self.settings

        # ---------- INTERNAL I2C ----------
        if not s or s.get("in.int_i2c", True):
            sda = s.get("in.int_i2c_sda", 3)
            scl = s.get("in.int_i2c_scl", 4)
            freq = s.get("in.int_i2c_freq", 100000)
            Pin(sda, Pin.IN, Pin.PULL_UP)
            Pin(scl, Pin.IN, Pin.PULL_UP)

            try:
                bus = SoftI2C(
                    scl=Pin(scl),
                    sda=Pin(sda),
                    freq=100000
                )
                self.i2c_buses["internal"] = bus
                print(f"I2C internal OK (SDA={sda}, SCL={scl})")
            except Exception as e:
                print("I2C internal failed:", e)

        # ---------- EXTERNAL I2C ----------
        if s and s.get("in.ext_i2c", False):
            sda = s.get("in.ext_i2c_sda", 12)
            scl = s.get("in.ext_i2c_scl", 13)
            freq = s.get("in.ext_i2c_freq", 100000)
            Pin(sda, Pin.IN, Pin.PULL_UP)
            Pin(scl, Pin.IN, Pin.PULL_UP)

            try:
                bus = SoftI2C(
                    scl=Pin(scl),
                    sda=Pin(sda),
                    freq=100000
                )
                self.i2c_buses["external"] = bus
                print(f"I2C external OK (SDA={sda}, SCL={scl})")
            except Exception as e:
                print("I2C external failed:", e)

        # ---------- COMPATIBILITY SHIM ----------
        # allows old drivers using hw.i2c to still work
        if "internal" in self.i2c_buses:
            self.i2c = self.i2c_buses["internal"]
        elif "external" in self.i2c_buses:
            self.i2c = self.i2c_buses["external"]
        else:
            self.i2c = None

    # =========================
    # GET I2C BUS
    # =========================
    def get_i2c(self, name):
        return self.i2c_buses.get(name)

    # =========================
    # LIST AVAILABLE BUSES
    # =========================
    def list_i2c(self):
        return list(self.i2c_buses.keys())

    # =========================
    # DEBUG SCAN
    # =========================
    def scan_all(self):
        print("I2C scan:")
        for name, bus in self.i2c_buses.items():
            try:
                devices = bus.scan()
                print(f"  {name}: {devices}")
            except Exception as e:
                print(f"  {name}: FAILED ({e})")


# =========================
# GLOBAL INSTANCE SYSTEM
# =========================

hw = None  # global reference used by drivers


def init(settings=None):
    global hw
    hw = Hardware(settings)
    return hw