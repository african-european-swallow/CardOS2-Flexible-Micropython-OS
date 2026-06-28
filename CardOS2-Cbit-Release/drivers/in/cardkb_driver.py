from machine import I2C, Pin
from core.hardware import hw


class Driver:
    CAPABILITIES = ["keyboard", "dpad", "action"]
    I2C_SUPPORT = ["internal", "external"]
    
    SHARED_CAP_GROUPS = [["keyboard", "action"]]

    def __init__(self):
        self.present = False
        self.i2c = None
        self.addr = 0x5F

        self.last_key = 0

        # ONE-FRAME PULSE VALUE
        self.frame_key = None

        self.KEYS = {
            180: "LEFT",
            181: "UP",
            182: "DOWN",
            183: "RIGHT",

            8:  "BACKSPACE",
            9:  "TAB",
            13: "ENTER",
            27: "ESC",
            32: "SPACE",
        }
        
        self.ACTION_KEYS = {
            ord("n"): "A",
            ord("m"): "B",
            ord("h"): "X",
            ord("j"): "Y",
            ord("i"): "START",
            ord("o"): "SELECT",
        }

    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
        preferred = settings.get("i2c.preferred") if settings else None
        bus_order = list(self.I2C_SUPPORT)

        if preferred in bus_order:
            bus_order.remove(preferred)
            bus_order.insert(0, preferred)

        for bus_name in bus_order:
            i2c = hw.get_i2c(bus_name)
            if not i2c:
                continue

            try:
                if self.addr in i2c.scan():
                    self.i2c = i2c
                    self.present = True
                    return
            except:
                pass

        self.present = False
        
    def disconnect(self):
        self.present = False
        self.i2c = None
    
    def probe(self):
        try:
            return self.addr in self.i2c.scan()
        except:
            return False
    
    # =========================
    # LOW LEVEL READ
    # =========================
    def _read(self):
        if not self.i2c:
            return 0

        try:
            data = self.i2c.readfrom(self.addr, 1)
            if not data:
                return 0
            return data[0]
        except:
            return 0

    # =========================
    # DECODE
    # =========================
    def _decode(self, key):
        return self.KEYS.get(key)

    # =========================
    # POLL (ONE FRAME PULSE)
    # =========================
    def poll(self):
        key = self._read()

        if key != 0:
            self.last_key = key
            self.frame_key = key
        else:
            self.frame_key = None  # <-- IMPORTANT: expire after frame

    # =========================
    # DPAD
    # =========================
    def _get_dpad(self):
        if not self.frame_key:
            return []

        value = self._decode(self.frame_key)

        if value in ("LEFT", "RIGHT", "UP", "DOWN"):
            return [value]

        if value == "ENTER":
            return ["CENTER"]

        return []

    # =========================
    # KEYBOARD
    # =========================
    def _get_keyboard(self):
        if not self.frame_key:
            return []

        value = self._decode(self.frame_key)

        # Only ignore true non-character controls
        if value in ("TAB", "ESC", "BACKSPACE", "SPACE"):
            return [value]

        # arrows ARE allowed now
        if value in ("LEFT", "RIGHT", "UP", "DOWN", "ENTER"):
            return [value]

        # normal ASCII keys
        try:
            return [chr(self.frame_key)]
        except:
            return []
        
    # =========================
    # ACTION
    # =========================
        
    def _get_action(self):
        if not self.frame_key:
            return []

        action = self.ACTION_KEYS.get(self.frame_key)
        if action:
            return [action]

        return []

    # =========================
    # GET
    # =========================
    def get(self, cap=None):
        if not self.present:
            return []

        if cap == "dpad":
            return self._get_dpad()

        if cap == "keyboard":
            return self._get_keyboard()
        
        if cap == "action":
            return self._get_action()

        return []