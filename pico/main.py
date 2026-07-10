from machine import I2CTarget, Pin, PWM
import time
from karl import *

# Muss zu PICO_ADDR in calliope/main.py passen.
I2C_ADDR = 0x42

# Der Calliope schreibt den Tanz per I2C in diesen Speicher:
#   mem[0] = Kommando-Nummer (aendert sich -> neuer Tanz liegt an)
#   mem[1] = Loop-Flag (1 = wiederholen)
#   mem[2] = Anzahl Moves
#   mem[3..] = Move-Nummern (1-5)
# Verkabelung (Expansion-Analog-Pins des Boards):
#   Calliope SDA -> GP26, Calliope SCL -> GP27, GND -> GND
# Falls die Pins anders beschriftet sind: es geht jedes benachbarte
# gerade/ungerade GP-Paar (gerade = SDA, ungerade = SCL). Die id muss
# zum Paar passen: GP0/1, GP4/5, GP8/9, GP12/13, GP16/17, GP20/21 -> id=0
#                  GP2/3, GP6/7, GP10/11, GP14/15, GP18/19, GP26/27 -> id=1
# Braucht MicroPython >= 1.26!
mem = bytearray(64)
i2c_target = I2CTarget(1, addr=I2C_ADDR, mem=mem, sda=Pin(26), scl=Pin(27))






def dance_1():
    sleep(0.2)
    right_foot.angle(30)
    left_foot.angle(-30)
    sleep(0.2)
    right_foot.angle(-30)
    left_foot.angle(30)
    sleep(0.2)
    reset()
    time.sleep(0.1)

def dance_2():
    sleep(0.2)
    right_foot.angle(-90)
    left_foot.angle(90)
    sleep(0.2)
    reset()
    time.sleep(0.1)


def dance_3():
    sleep(0.2)
    right_leg.angle(51)
    left_leg.angle(51)
    sleep(0.35)
    right_leg.angle(-51)
    left_leg.angle(-51)
    sleep(0.35)
    reset()
    time.sleep(0.1)


def dance_4():
    sleep(0.2)
    right_foot.angle(40)
    left_foot.angle(-40)
    sleep(0.2)
    sleep(0.2)
    right_leg.angle(30)
    left_leg.angle(30)
    sleep(0.2)
    right_leg.angle(-30)
    left_leg.angle(-30)
    sleep(0.2)
    reset()
    time.sleep(0.1)


def dance_5():
    left_leg.angle(30)
    sleep(0.3)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    left_foot.angle(40)
    sleep(0.2)
    left_foot.angle(0)
    sleep(0.2)
    reset()
    time.sleep(0.1)


DANCES = {1: dance_1, 2: dance_2, 3: dance_3, 4: dance_4, 5: dance_5}

last_seq = 0

while True:
    if mem[0] != last_seq:
        last_seq = mem[0]
        loop_flag = mem[1]
        count = mem[2]
        dance = list(mem[3:3 + count])

        i = 0
        while dance and mem[0] == last_seq:
            fn = DANCES.get(dance[i])
            if fn:
                fn()
            i += 1
            if i >= len(dance):
                if not loop_flag:
                    break
                i = 0
    time.sleep_ms(10)


