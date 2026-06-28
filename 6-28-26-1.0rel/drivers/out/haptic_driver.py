# core/haptic_driver.py

import time
from machine import Pin
import drv2605
from core.hardware import hw

class Driver:
    CAPABILITIES = ["tick", "ok", "error", "buzz", "alert_short", "alert_long", 'notify']

    I2C_SUPPORT = ["internal", "external"]

    EFFECT_MAP = {
        "tick": 1,          # Strong Click
        "ok": 11,           # Double Click
        "notify": 14,       # Strong Buzz
        "buzz": 47,         # Buzz 1
        "alert_short": 15,  # 750 ms Alert
        "alert_long": 16,   # 1000 ms Alert
        "error": 16,        # 1000 ms Alert
    }

    def __init__(self):
        self.present = False
        self.i2c = None
        self.drv = None

    # =========================
    # CONNECT
    # =========================
    def connect(self, settings=None):
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
                self.i2c = i2c
                self.drv = drv2605.DRV2605(self.i2c)
                self.present = True
                return
            except Exception as e:
                pass
        self.present = False

    # =========================
    # DISCONNECT
    # =========================
    def disconnect(self):
        if self.drv:
            try:
                self.drv.stop()
            except Exception as e:
                pass
        self.drv = None
        self.i2c = None
        self.present = False

    # =========================
    # PLAY EFFECT
    # =========================
    def play(self, cap):
        if not self.present or not self.drv:
            return

        effect_id = self.EFFECT_MAP.get(cap, 1)
        try:
            self.drv.sequence[0] = drv2605.Effect(effect_id)
            self.drv.play()
            #time.sleep(0.1)
            #self.drv.stop()
        except Exception as e:
            pass