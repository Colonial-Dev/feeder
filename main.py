import asyncio
import wlan
import rtc

from machine import Pin
from utime import sleep_ms
from microdot import Microdot # type: ignore

LO = 0
HI = 1

OUT = LO
IN  = HI

class Stepper:
    def reset(self):
        self.EN.value(HI)
        self.STP.value(LO)
        self.DIR.value(LO)
        self.MS1.value(LO)
        self.MS2.value(LO)

    def step(self, count):
        count = int(count / 100)

        def do(direction, steps):
            self.DIR.value(direction)

            for i in range(0, steps):
                self.STP.value(HI)
                sleep_ms(1)
                self.STP.value(LO)
                sleep_ms(1)

        # This alternating pattern - 200 steps out, 100 steps in -
        # helps prevent jams and clogs in the auger mechanism.
        for i in range(0, count):
            do(OUT, 200)
            do(IN, 100)

    def enable(self):
        self.EN.value(LO)

    def disable(self):
        self.EN.value(HI)

    def __init__(self):
        self.STP = Pin(26, Pin.OUT)
        self.DIR = Pin(27, Pin.OUT)
        self.MS1 = Pin(28, Pin.OUT)
        self.MS2 = Pin(4, Pin.OUT)
        self.EN  = Pin(3, Pin.OUT)

        self.reset()

wlan.connect()

app      = Microdot()
clock    = rtc.RTC(-5)
schedule = eval(
    open('schedule.dat').read()
)
stepper  = Stepper()

@app.route('/')
async def root(req):
    with open("schedule.dat", "r") as file:
        schedule = file.read().strip("[] \n")
        now      = clock.get()
        now       = f"{now[0]:02}:{now[1]:02}:{now[2]:02}"

        with open("www/index.html", "r") as template:
            return template.read().format(schedule=schedule, now=now).encode(), {'Content-Type': 'text/html'}
        
@app.route('/schedule', methods=['POST'])
async def update_schedule(req):
    global schedule

    schedule = eval(f"[{req.form.get('schedule')}]")

    with open("schedule.dat", "w+") as file:
        file.write(f"{schedule}")
    
@app.route('/feed', methods=['POST'])
async def manual_feed(req):
    count = int(req.form.get('steps'))

    stepper.enable()
    stepper.step(count)
    stepper.disable()

async def watch_schedule():
    global schedule

    while True:
        nh, nm, _ = clock.get()

        for entry in schedule:
            print(entry)
            h, m, s = entry

            if h == nh and m == nm:
                print(f"Feeding time! It is {nh:02}:{nm:02} and we are dispensing {s} steps of food.")
                
                stepper.enable()
                stepper.step(s)
                stepper.disable()

                # After feeding, sleep for 60 seconds to avoid re-firing.
                await asyncio.sleep(60)
                break
        
        await asyncio.sleep(15)
            

async def main():
    server = asyncio.create_task(
        app.start_server(host = '0.0.0.0', port = 80, debug = True)
    )

    asyncio.create_task(watch_schedule())

    await server

if __name__ == "__main__":
    asyncio.run(main())