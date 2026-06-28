# core/hardware.py

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
        
        for i in s.get('i2c.list'):
            # ---------- I2C ----------
            sda = s.get(f"i2c.{i}.i2c_sda")
            scl = s.get(f"i2c.{i}.i2c_scl")
            freq = s.get(f"i2c.{i}.i2c_freq", 100000)
            Pin(sda, Pin.IN, Pin.PULL_UP)
            Pin(scl, Pin.IN, Pin.PULL_UP)

            try:
                bus = SoftI2C(
                    scl=Pin(scl),
                    sda=Pin(sda),
                    freq=freq
                )
                self.i2c_buses[i] = bus
                print(f"I2C {i} OK (SDA={sda}, SCL={scl})")
            except Exception as e:
                print(f"I2C {i} failed:", e)

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