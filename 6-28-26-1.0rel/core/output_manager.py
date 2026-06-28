# core/output_manager.py

import os
import time

class Output:
    HOTSWAP_INTERVAL = 32.5  # seconds between device presence checks

    def __init__(self, settings=None):
        self.drivers = []
        self.settings = settings
        self.capabilities = {}  # cap_name -> list of driver instances
        self.last_scan = 0
        self.error = None

    # =========================
    # LOAD DRIVERS
    # =========================
    def scan_drivers(self):
        self.drivers = []
        self.capabilities = {}

        drivers = self.drivers
        capabilities = self.capabilities
        settings = self.settings

        for file in os.listdir("drivers/out"):
            if not file.endswith("_driver.py"):
                continue

            name = file[:-3]

            try:
                module = __import__("drivers.out." + name, None, None, ("Driver",))
                DriverClass = getattr(module, "Driver", None)
                if not DriverClass:
                    continue

                # settings toggle 
                if settings:
                    key = "use_" + name[:-7]
                    if not settings.get(key, True):
                        continue

                drv = DriverClass()

                # cache connect
                connect = getattr(drv, "connect", None)
                if connect:
                    try:
                        connect(settings)
                    except TypeError:
                        connect()

                # cache play + disconnect
                play = getattr(drv, "play", None)
                disconnect = getattr(drv, "disconnect", None)

                # capabilities as tuple
                caps = tuple(getattr(drv, "CAPABILITIES", ()))

                drivers.append({
                    "name": name,
                    "driver": drv,
                    "caps": caps,
                    "play": play,
                    "disconnect": disconnect,
                })

                # build capability map (store play directly is faster)
                for cap in caps:
                    if cap not in capabilities:
                        capabilities[cap] = []
                    if play:
                        capabilities[cap].append(play)

            except Exception as e:
                if self.error:
                    self.error.report("Output", f"driver load failed: {name}", e, level="warn")

        self.last_scan = time.time()
        
    # =========================
    # HOT-SWAP CHECK
    # =========================
    def update(self):
        now = time.time()
        if now - self.last_scan <= self.HOTSWAP_INTERVAL:
            return

        drivers = self.drivers
        settings = self.settings

        for entry in drivers:
            drv = entry["driver"]

            if getattr(drv, "present", True):
                continue

            connect = getattr(drv, "connect", None)
            if not connect:
                continue

            try:
                try:
                    connect(settings)
                except TypeError:
                    connect()
            except Exception as e:
                if self.error:
                    self.error.report("Output", f"hotswap failed: {entry['name']}", e, level="warn")

        self.last_scan = now

    # =========================
    # MAIN INTERFACE
    # =========================
    def feedback(self, cap):
        self.update()

        plays = self.capabilities.get(cap)
        if not plays:
            return

        for play in plays:
            try:
                play(cap)
            except Exception as e:
                print("Driver feedback error:", e)

    # =========================
    # DISCONNECT ALL DRIVERS
    # =========================
    def disconnect_drivers(self):
        for entry in self.drivers:
            disconnect = entry["disconnect"]
            if not disconnect:
                continue
            try:
                disconnect()
            except Exception as e:
                print("Driver disconnect failed:", entry["name"], e)
