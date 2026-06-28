# core/sdcard_manager.py

from core.hardware import hw
import machine
import time
import uos
import sdcard
import sys


class SDManager:
    HOTSWAP_INTERVAL = 10.0

    def __init__(self, settings=None):
        self.last_check = 0

        self.present = False

        self.sd = None
        self.spi = None
        self.cs = None

        # =========================
        # SETTINGS
        # =========================

        self.cs_pin = int(settings.get("sd.cs", 10))
        self.sck_pin = int(settings.get("sd.sck", 18))
        self.mosi_pin = int(settings.get("sd.mosi", 17))
        self.miso_pin = int(settings.get("sd.miso", 16))

        self.spi_bus = int(settings.get("sd.spi_bus", 1))

        # =========================
        # DETECT PIN
        # =========================

        self.use_detect = settings.get("sd.use_detect", False)
        self.detect_pin = int(settings.get("sd.detect_pin", 11))

        if self.use_detect:
            self.sd_detect = machine.Pin(self.detect_pin,machine.Pin.IN,machine.Pin.PULL_UP)

        del settings

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):
        now = time.time()

        if now - self.last_check < self.HOTSWAP_INTERVAL:
            return

        self.last_check = now

        # -------------------------
        # DETECT PIN MODE
        # -------------------------

        if self.use_detect:
            inserted = self.check()

            if inserted and not self.present:
                self.mount_sd()

            elif not inserted and self.present:
                self.unmount_sd()

        # -------------------------
        # NO DETECT PIN
        # -------------------------

        else:
            if not self.present:
                self.mount_sd()

            else:
                if not self.probe():
                    print("SD card removed?")
                    self.unmount_sd()

    # =========================================================
    # MOUNT
    # =========================================================

    def mount_sd(self):
        if self.present:
            return True

        try:
            # =========================
            # FORCE CLEAN OLD STATE
            # =========================

            try:
                uos.umount("/sd")
            except:
                pass

            self.present = False
            self.sd = None

            # fully kill old SPI peripheral
            if self.spi:
                try:
                    self.spi.deinit()
                except:
                    pass

            self.spi = None

            time.sleep_ms(100)

            # =========================
            # RECREATE SPI
            # =========================

            self.spi = machine.SPI(
                self.spi_bus,
                baudrate=400000,
                polarity=0,
                phase=0,
                bits=8,
                firstbit=machine.SPI.MSB,
                sck=machine.Pin(self.sck_pin),
                mosi=machine.Pin(self.mosi_pin),
                miso=machine.Pin(self.miso_pin)
            )

            self.cs = machine.Pin(self.cs_pin, machine.Pin.OUT)

            # deselect card
            self.cs.value(1)

            # SD cards need >=74 clocks with CS high
            for _ in range(16):
                self.spi.write(b'\xff')

            time.sleep_ms(20)

            # =========================
            # CREATE SD OBJECT
            # =========================

            self.sd = sdcard.SDCard(self.spi,self.cs)

            # =========================
            # MOUNT
            # =========================

            uos.mount(self.sd, "/sd")

            # faster runtime speed after init
            self.spi.init(baudrate=10_000_000)

            # =========================
            # IMPORT PATH
            # =========================

            import sys

            if "/sd" not in sys.path:
                sys.path.append("/sd")

            # probe file
            try:
                with open("/sd/.probe", "w") as f:
                    f.write("ok")
            except:
                pass

            self.present = True

            print("SD mounted")

            return True

        except Exception as e:
            print("SD mount failed:", e)

            self.cleanup()

            return False

    # =========================================================
    # UNMOUNT
    # =========================================================

    def unmount_sd(self):
        try:
            uos.umount("/sd")
        except:
            pass

        self.cleanup()

        print("SD unmounted")

    # =========================================================
    # CLEANUP
    # =========================================================

    def cleanup(self):
        self.present = False

        self.sd = None

        if self.spi:
            try:
                self.spi.deinit()
            except:
                pass

        self.spi = None
        self.cs = None

    # =========================================================
    # PROBE
    # =========================================================

    def probe(self):
        try:
            with open("/sd/.probe", "r"):
                pass

            return True

        except Exception:
            return False

    # =========================================================
    # STATUS
    # =========================================================

    def is_mounted(self):
        return self.present

    def get_path(self):
        if self.present:
            return "/sd"

        return None

    # =========================================================
    # CARD DETECT
    # =========================================================

    def check(self):
        """
        Returns True if inserted.
        """

        return self.sd_detect.value() == 1
    