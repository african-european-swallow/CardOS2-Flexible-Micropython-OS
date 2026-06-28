from lib.seesaw import Seesaw
from core.hardware import hw


class Driver:
    CAPABILITIES = ["action", "dpad"]
    I2C_SUPPORT = ["external"]

    BUTTON_MAP = {
        0: "SELECT",
        1: "B",
        2: "Y",
        5: "A",
        6: "X",
        16: "START",
    }

    def __init__(self):
        self.present = False
        self.ss = None
        self.i2c = None
        self.ctx = None

        # joystick channels
        self.JOY_X = 16
        self.JOY_Y = 15

        self.BUTTON_PINS = [0, 1, 2, 5, 6, 16]

        self.action_out = []
        self.dpad_out = []

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
                ss = Seesaw(i2c)
                ss.init()

                for pin in self.BUTTON_PINS:
                    ss.pin_config(pin, mode=0, pull=1)

                self.ss = ss
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
        self.ss = None
        self.i2c = None

    def probe(self):
        return self.ss is not None

    # =========================
    # SINGLE FRAME READ
    # =========================
    def _read_frame(self):
        if not self.ss:
            return None, (0, 0)

        try:
            gpio = self.ss.read_gpio_bulk()
            x = self.ss.analog_read(self.JOY_X)
            y = self.ss.analog_read(self.JOY_Y)
            return gpio, (x, y)

        except OSError:
            # device disappeared = mark as gone
            self.present = False
            return None, (0, 0)

    # =========================
    # BUTTON DECODER 
    # =========================
    def _decode_buttons(self, gpio):
        pressed = []

        for pin in self.BUTTON_PINS:
            byte_index = 3 - (pin // 8)

            if pin >= 32:
                byte_index += 4
                pin_mod = pin - 32
            else:
                pin_mod = pin

            if (gpio[byte_index] >> (pin_mod % 8)) & 1 == 0:
                pressed.append(pin)

        return pressed

    # =========================
    # POLL
    # =========================
    def poll(self):
        if not self.present or not self.ss:
            self.action_out = []
            self.dpad_out = []
            return

        gpio, (joy_x, joy_y) = self._read_frame()
        
        if gpio is None:
            self.action_out = []
            self.dpad_out = []
            return
        # =========================
        # ACTION
        # =========================
        buttons = self._decode_buttons(gpio)

        self.action_out = []
        for b in buttons:
            if b in self.BUTTON_MAP:
                self.action_out.append(self.BUTTON_MAP[b])

        # =========================
        # DPAD
        # =========================
        self.dpad_out = []

        if joy_x >= 716:
            self.dpad_out.append("DOWN")
        elif joy_x <= 292:
            self.dpad_out.append("UP")

        if joy_y >= 716:
            self.dpad_out.append("LEFT")
        elif joy_y <= 292:
            self.dpad_out.append("RIGHT")

    # =========================
    # INPUT
    # =========================
    def get(self, cap=None):
        if cap == "action":
            return self.action_out
        if cap == "dpad":
            return self.dpad_out
        return []