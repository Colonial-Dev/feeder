import socket
import struct
import time

from machine import RTC as Clock

class RTC:
    def __init__(self, offset):
        NTP_DELTA = 2208988800
        host      = "pool.ntp.org"

        self.c    = Clock()
        self.off  = offset

        # Query the NTP server
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B

        addr = socket.getaddrinfo(host, 123)[0][-1]
        s    = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            s.settimeout(5)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        except Exception as e:
            print(f"NTP query timeout: {e}")
        finally:
            s.close()

        # Set our internal time
        val = struct.unpack("!I", msg[40:44])[0]
        tm = val - NTP_DELTA    
        t = time.gmtime(tm)

        self.c.datetime(
            (t[0],t[1],t[2],t[6]+1,t[3],t[4],t[5],0)
        )

    def get(self):
        # Y, M, D, Weekday, H, M, S, MS
        d = self.c.datetime()

        # Hour (offset), minute, second
        return (
            (d[4] + self.off) % 24,
            d[5],
            d[6]
        )
