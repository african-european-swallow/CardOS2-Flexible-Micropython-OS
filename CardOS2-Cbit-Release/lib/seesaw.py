# SPDX-FileCopyrightText: 2019 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from machine import I2C
import struct
import time


_SIGNALS = (2, 3, 40, 41, 11, 10, 9, 8)
_PWMS = (14, 15, 16, 17, 19, 18, 22, 23, 42, 43, 12, 13)
_SERVOS = (17, 16, 15, 14)
_MOTORS = (22, 23, 19, 18)
_DRIVES = (13, 12, 43, 42)
_TOUCHES = (0, 1, 2, 3)

_ADDR = 0x50

reg_buf = bytearray(2)
pwm_buf = bytearray(3)


class Seesaw:
    def __init__(self, i2c, addr=_ADDR):
        self.i2c = i2c
        self.addr = addr

    # =========================
    # LOW LEVEL
    # =========================
    def _read(self, reghi, reglo, n, delay_s=0.01):
        reg_buf[0] = reghi
        reg_buf[1] = reglo

        self.i2c.writeto(self.addr, reg_buf)
        #time.sleep(delay_s)

        return self.i2c.readfrom(self.addr, n)

    def _write(self, reghi, reglo, cmd):
        reg_buf[0] = reghi
        reg_buf[1] = reglo

        self.i2c.writeto(self.addr, reg_buf + cmd)

    # =========================
    # INIT
    # =========================
    def init(self):

        reg_buf[0] = 0x7F
        reg_buf[1] = 0xFF

        self.i2c.writeto(self.addr, reg_buf)

    # =========================
    # ANALOG
    # =========================
    def analog_read(self, signal):
        return struct.unpack(
            ">H",
            self._read(0x09, 0x07 + signal - 1, 2)
        )[0]

    # =========================
    # GPIO
    # =========================
    def pin_config(self, pin, mode, pull=None, val=None):
        if pin >= 32:
            cmd = struct.pack(">I", 1 << (pin - 32))
            cmd = bytearray(4) + cmd
        else:
            cmd = struct.pack(">I", 1 << pin)

        if 0 <= mode <= 1:
            self._write(0x01, 0x03 - mode, cmd)

        if pull is not None and 0 <= pull <= 1:
            self._write(0x01, 0x0C - pull, cmd)

        if val is not None and 0 <= val <= 1:
            self._write(0x01, 0x06 - val, cmd)

    def read_gpio_bulk(self):
        if not hasattr(self, "_gpio_cache_time"):
            self._gpio_cache_time = 0
            self._gpio_cache = None

        now = time.ticks_ms()

        if self._gpio_cache is None or now - self._gpio_cache_time > 10:
            self._gpio_cache = self._read(0x01, 0x04, 8)
            self._gpio_cache_time = now

        return self._gpio_cache

    def read_digital(self, signal):
        pin = _SIGNALS[signal - 1]

        self.pin_config(pin, 0, 1, 1)

        ret = self._read(0x01, 0x04, 8)

        b = 0

        if pin > 32:
            b = 4
            pin -= 32

        b += 3 - (pin // 8)

        return (ret[b] & 1 << (pin % 8)) != 0

    def write_digital(self, signal, val):
        self.pin_config(_SIGNALS[signal - 1], 1, 0, val)

    # =========================
    # PWM
    # =========================
    def pwm_write(self, pwm, val):
        pwm_buf[0] = _PWMS.index(pwm)
        pwm_buf[1] = val >> 8
        pwm_buf[2] = val & 0xFF

        self._write(0x08, 0x01, pwm_buf)

    def set_pwmfreq(self, pwm, freq):
        pwm_buf[0] = _PWMS.index(pwm)
        pwm_buf[1] = freq >> 8
        pwm_buf[2] = freq & 0xFF

        self._write(0x08, 0x02, pwm_buf)

    # =========================
    # ENCODER
    # =========================
    def encoder_position(self, encoder=0):
        return struct.unpack(
            ">i",
            self._read(0x11, 0x00 + encoder * 0x10, 4)
        )[0]

    def encoder_delta(self, encoder=0):
        return struct.unpack(
            ">i",
            self._read(0x11, 0x04 + encoder * 0x10, 4)
        )[0]

    def encoder_enable_interrupt(self, encoder=0, enable=True):
        val = b'\x01' if enable else b'\x00'
        self._write(0x11, 0x10 + encoder * 0x10, val)

    def encoder_set_mode(self, encoder=0, mode=0x00):
        self._write(
            0x11,
            0x0E + encoder * 0x10,
            bytes([mode])
        )