from machine import Pin
import mpr121
from core.hardware import hw


class Driver:
    CAPABILITIES = ["touchpad", "action"]
    I2C_SUPPORT = ["internal"]
    
    SHARED_CAP_GROUPS = [["action", "touchpad"]]

    ACTION_MAP = {
        0: "A",
        1: "B",
        3: "X",
        4: "Y",
        6: "START",
        7: "SELECT",
    }

    def __init__(self):
        self.present = False
        self.mpr = None
        self.i2c = None

        self.last_mask = 0

        # cached per-frame outputs
        self.numpad_out = []
        self.action_out = []

        self.ctx = None

    # =========================
    # CONTEXT
    # =========================
    def set_ctx(self, ctx):
        self.ctx = ctx

    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
        self.present = False

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
                self.mpr = mpr121.MPR121(i2c, 0x5B)
                self.i2c = i2c
                self.present = True
                return

            except Exception as e:
                pass
        self.present = False

    # =========================
    # DISCONNECT
    # =========================
    def disconnect(self):
        self.present = False
        self.mpr = None
        self.i2c = None

    def probe(self):
        return self.mpr is not None

    # =========================
    # FRAME UPDATE (ALL COMPUTATION HERE)
    # =========================
    def poll(self):
        if not self.present or not self.mpr:
            self.numpad_out = []
            self.action_out = []
            return

        mask = self.mpr.touched()
        new_press = mask & (~self.last_mask)

        # haptic feedback once per frame
        if new_press and self.ctx:
            try:
                self.ctx.output.feedback("tick")
            except:
                pass

        self.last_mask = mask

        # =========================
        # NUMPAD OUTPUT
        # =========================
        self.numpad_out = [
            str(i) for i in range(12) if mask & (1 << i)
        ]

        # =========================
        # ACTION OUTPUT
        # =========================
        self.action_out = []
        for i in range(12):
            if mask & (1 << i) and i in self.ACTION_MAP:
                self.action_out.append(self.ACTION_MAP[i])
        #print("MASK:", mask)
        #print("ACTION OUT:", self.action_out)

    # =========================
    # INPUT (NO COMPUTATION HERE)
    # =========================
    def get(self, cap=None):
        if cap == "numpad" or cap == "touchpad":
            return self.numpad_out

        if cap == "action":
            return self.action_out

        return []