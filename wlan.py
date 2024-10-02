import rp2
import network 
import utime

from machine import Pin
from secrets import networks

def connect():
    rp2.country('US')

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for net in networks:
        ticks = 0

        print(f"Attempting to connect to AP {net['ssid']}...")

        wlan.connect(net['ssid'], net['pass'])
        wlan.ifconfig(net['ifconf'])

        while ticks < 10:
            print('.', end='')
            utime.sleep(1)
            ticks += 1

        if wlan.isconnected():
            print(f"Connection established to AP {net['ssid']}.")
            Pin('LED', Pin.OUT).value(1)
            break
        else:
            print(f"Connection to AP {net['ssid']} failed.")
            continue

