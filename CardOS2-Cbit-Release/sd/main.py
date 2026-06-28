from machine import Pin, PWM
import time

# Pin 13 is the internal LED on Teensy 4.1
# Frequency of 1000Hz provides smooth fading without flickering
led = PWM(Pin('D13'), freq=1000)

while True:
    # Fade in: 0 to 65535 (max brightness for 16-bit PWM)
    for i in range(0, 65536, 256):
        led.duty_u16(i)
        time.sleep(0.01)
        
    # Fade out: 65535 down to 0
    for i in range(65535, -1, -256):
        led.duty_u16(i)
        time.sleep(0.01)
