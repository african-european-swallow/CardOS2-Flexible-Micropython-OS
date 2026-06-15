# drivers/in/battery_driver.py

from core.hardware import hw

class Driver:
    CAPABILITIES = ["battery"]

    # supports buses
    I2C_SUPPORT = ["internal"] #"external"
    SENSOR=True #not yet used

    def __init__(self):
        self.present = False
        self.i2c = None
        self.max = None

    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
        from max1704x import max1704x

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
                self.max = max1704x(i2c)

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
        self.max = None
        
    def probe(self):
        return self.max is not None
        
    # =========================
    # INPUT
    # =========================
    def read(self, cap):
        if not self.present:
            return []

        if cap == "battery":
            return [self.max.getSoc()]

        return []