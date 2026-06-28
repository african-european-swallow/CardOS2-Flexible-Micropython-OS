# core/input_manager.py

import os
import time


class Input:
    HOTSWAP_INTERVAL = 5.0

    def __init__(self, settings=None):
        self.devices = []
        self.settings = settings
        self.ctx = None
        self.claimed_caps = set()

        # =========================
        # GLOBAL KEY STATE
        # =========================
        self.pressed = []
        self.last = []

        self.just_pressed = []
        self.just_released = []

        # =========================
        # CAP STATE
        # =========================
        self.cap_current = {}        # cap -> keys currently down
        self.cap_last = {}           # cap -> keys last frame

        self.cap_just_pressed = {}   # off -> on this frame
        self.cap_just_released = {}  # on -> off this frame
        
        self.sensor_values = {}

        self.last_scan = 0

        self.quit_driver = None
        self.quit = False

    # =========================
    # LOAD DRIVERS
    # =========================
    def scan_drivers(self):
        self.devices = []
        self.cap_current = {}
        self.cap_last = {}
        self.cap_just_pressed = {}
        self.cap_just_released = {}

        for file in os.listdir("drivers/in"):
            if not file.endswith("_driver.py"):
                continue

            name = file[:-3]

            try:
                module = __import__("drivers.in." + name, None, None, ("Driver",))
                DriverClass = getattr(module, "Driver", None)
                if not DriverClass:
                    continue

                if self.settings:
                    key = "use_" + name[:-7]
                    if not self.settings.get(key, True):
                        continue

                drv = DriverClass()

                if self.ctx and hasattr(drv, "set_ctx"):
                    drv.set_ctx(self.ctx)

                connect = getattr(drv, "connect", None)
                if connect:
                    try:
                        connect(self.settings)
                    except TypeError:
                        connect()

                caps = tuple(getattr(drv, "CAPABILITIES", ()))
                get = getattr(drv, "get", None)
                sensor = getattr(drv, "SENSOR", False)

                if not file.endswith("system_quit_driver.py"):
                    self.devices.append({
                        "driver": drv,
                        "capabilities": caps,
                        "get": get,
                        "sensor": sensor,
                    })
                else:
                    self.quit_driver = {
                        "driver": drv,
                        "capabilities": caps,
                        "get": get,
                        "sensor": sensor,
                    }

                for cap in caps:
                    if cap not in self.cap_current:
                        self.cap_current[cap] = []
                        self.cap_last[cap] = []
                        self.cap_just_pressed[cap] = []
                        self.cap_just_released[cap] = []

            except Exception as e:
                if self.ctx and self.ctx.error:
                    self.ctx.error.report(
                        "Input",
                        f"driver load failed: {name}",
                        e,
                        level="warn"
                    )

        self.last_scan = time.time()

    # =========================
    # HOTSWAP
    # =========================
    def hot_swap_check(self):
        now = time.time()
        if now - self.last_scan > self.HOTSWAP_INTERVAL:
            for dev in self.devices:
                drv = dev["driver"]

                if hasattr(drv, "present") and not drv.present:
                    if self.ctx and hasattr(drv, "set_ctx"):
                        drv.set_ctx(self.ctx)

                    try:
                        try:
                            drv.connect(self.settings)
                        except TypeError:
                            drv.connect()
                    except Exception as e:
                        if self.ctx and self.ctx.error:
                            self.ctx.error.report(
                                "Input",
                                "hotswap failed",
                                e,
                                level="warn"
                            )

            self.last_scan = now

    # =========================
    # UPDATE 
    # =========================
    def update(self):
        self.hot_swap_check()

        # =========================
        # GLOBAL FRAME RESET
        # =========================
        prev_global = self.pressed
        self.pressed = []

        for cap in self.cap_current:
            self.cap_current[cap] = []
            self.cap_just_pressed[cap] = []
            self.cap_just_released[cap] = []

        # =========================
        # POLL DRIVERS
        # =========================
        for dev in self.devices:
            drv = dev["driver"]

            if hasattr(drv, "poll"):
                drv.poll()

        # =========================
        # UPDATE SENSORS
        # =========================
        for dev in self.devices:
            if not dev["sensor"]:
                continue

            drv = dev["driver"]

            if hasattr(drv, "read"):
                try:
                    for cap in dev["capabilities"]:
                        self.sensor_values[cap] = drv.read(cap)
                except Exception as e:
                    print("Sensor error:", e)

        # =========================
        # COLLECT INPUT
        # =========================
        for dev in self.devices:
            if dev["sensor"]:
                continue

            get = dev["get"]
            if not get:
                continue

            try:
                for cap in dev["capabilities"]:
                    if self.cap_blocked(dev, cap):
                        continue

                    keys = get(cap)
                    if not keys:
                        continue

                    for k in keys:
                        if k not in self.pressed:
                            self.pressed.append(k)

                        if k not in self.cap_current[cap]:
                            self.cap_current[cap].append(k)

            except Exception as e:
                print("Driver error:", e)

        # =========================
        # GLOBAL DELTAS
        # =========================
        self.just_pressed = []
        self.just_released = []

        for k in self.pressed:
            if k not in prev_global:
                self.just_pressed.append(k)

        for k in prev_global:
            if k not in self.pressed:
                self.just_released.append(k)

        # =========================
        # CAP DELTAS
        # =========================
        for cap in self.cap_current:
            current = self.cap_current[cap]
            previous = self.cap_last.get(cap, [])

            self.cap_just_pressed[cap] = [
                k for k in current if k not in previous
            ]

            self.cap_just_released[cap] = [
                k for k in previous if k not in current
            ]

            self.cap_last[cap] = current.copy()

        if self.quit_driver:
            get = self.quit_driver["get"]
            self.quit = get("quit")

    # =========================
    # GLOBAL API
    # =========================
    def get_sensor(self, cap, default=None):
        return self.sensor_values.get(cap, default)
    
    def get(self):
        return self.pressed

    def get_pressed(self):
        return self.just_pressed

    def get_released(self):
        return self.just_released

    def is_down(self, key):
        return key in self.pressed

    def was_pressed(self, key):
        return key in self.just_pressed

    def was_released(self, key):
        return key in self.just_released

    # =========================
    # CAP API
    # =========================
    def get_cap(self, cap):
        return self.cap_current.get(cap, [])

    def is_down_cap(self, cap, key):
        return key in self.cap_current.get(cap, [])

    def get_pressed_cap(self, cap):
        return self.cap_just_pressed.get(cap, [])

    def get_released_cap(self, cap):
        return self.cap_just_released.get(cap, [])

    def was_pressed_cap(self, cap, key):
        return key in self.cap_just_pressed.get(cap, [])

    def was_released_cap(self, cap, key):
        return key in self.cap_just_released.get(cap, [])

    # =========================
    # ACTIVE CAPS
    # =========================
    def get_active_capabilities(self):
        active = []

        for dev in self.devices:
            drv = dev["driver"]

            # authoritative check
            try:
                if not drv.probe():
                    continue
            except:
                continue

            for cap in dev["capabilities"]:
                if cap not in active:
                    active.append(cap)

        return active

    def claim_caps(self, caps):
        # allow single string
        if isinstance(caps, str):
            caps = [caps]

        self.claimed_caps = set(caps)

    def clear_claims(self):
        self.claimed_caps = set()
        
    def get_claims(self):
        return list(self.claimed_caps)

    def has_claim(self, cap):
        return cap in self.claimed_caps

    def cap_blocked(self, dev, cap):
        drv = dev["driver"]

        groups = getattr(drv, "SHARED_CAP_GROUPS", [])

        for group in groups:
            if cap not in group:
                continue

            my_index = group.index(cap)

            # Any higher-priority claimed cap blocks me
            for higher_cap in group[:my_index]:
                if higher_cap in self.claimed_caps:
                    return True

        return False
    
