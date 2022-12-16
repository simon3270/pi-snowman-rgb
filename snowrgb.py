#!/usr/bin/python3

# SnowpiRGB plugged into pins 2, 4, 6, 8, 10, 12 as usual
# Optional PIR, 5V wire soldered to pins 2 or 4 at back of SnowPiRGB
#               ground to pin 34
#               signal to pin 36 (GPIO16)
# See https://maker.pro/raspberry-pi/tutorial/how-to-interface-a-pir-motion-sensor-with-raspberry-pi-gpio

# Uses PIR on BCM pin 16 (=GPIO16 = pin 36)
# SnowPi RGB currently uses PCM CLK (pin 18)

# Supports multiple Snowmen wired in series (the "-m" parameter)

#      11   10
#         9
#      2  5  8
#    1    4   7
#    0    3   6


# Import required libraries
import time
import random
import sys
try:
    from rpi_ws281x import PixelStrip, Color
except:
    print("Could not load rpi_ws281x module")
import argparse
import datetime
import threading

# PIR sensor signal GPIO pin
PIR_SENSE = 16

# LED strip configuration:
LED_COUNT = 12        # Number of LED pixels in each snowman.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 20   # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

BLACK=Color(0, 0, 0)
WHITE=Color(255, 255, 255)
RED=Color(255, 0, 0)
GREEN=Color(0, 255, 0)
BLUE=Color(0, 0, 255)
ORANGE=Color(255, 165, 0)
COLOR_LOOP=(WHITE, RED, GREEN, BLUE, ORANGE)

ARMS=(0, 1, 2, 8, 7, 6)
ARMS2=(6, 7, 8, 2, 1, 0)
ARML=(0, 1, 2)
ARMR=(6, 7, 8)
TIE=(5, 4, 3)
EYES=(10, 11)
EYELEFT=(10,)
EYELEFT=(11,)
NOSE=(9,)

# 'Snowman' Colors of all 12 LEDS, in order
LEDCOLORS=(WHITE, WHITE, WHITE, GREEN, GREEN, GREEN, WHITE, WHITE, WHITE, ORANGE, BLUE, BLUE)

# Set default Cheerlights colour to green
# This means we can use cheerlights colour in amy display,
# whether or not we are connecting to cheerlights.com
cheercolour = GREEN

random.seed()

# Global variables so that threads can communicate
insync = False
idlemen = 0

def datenow():
    # Return the current date and time as YYYY/MM/DD HH:MMM:SS
    return datetime.datetime.now().strftime("%F %T")

def hold_leds_add(hold_leds, baseLED, next):
    ''' Add a new tail entry to the list of LEDs turned on,
        so that  they can be turned off later.
        This stores the offest including the baseLED value,
        since the snowman being turned off will vary'''
    if type(next) is int:
        next = next + baseLED
    elif type(next) is tuple:
        next = tuple([x + baseLED for x in next])
    hold_leds.append(next)
    # Updates called hold_leds variable
    # No need to return the list

def hold_leds_release(hold_leds, hold_max, strip, wait_ms):
    ''' Remove the head of the hold_leds list and turn it off.
        Repeat until list is at max allowed length.
        Return updated list '''
    # If there are more than the expected number of LEDs to
    # turn off in the list, loop through removing them.
    # This keeps the list filled to hold_max during running,
    # and with hold_max=0 will drain the list.
    while len(hold_leds) > hold_max:
        head_led = hold_leds[0]
        hold_leds = hold_leds[1:]
        if type(head_led) is int:
            strip.setPixelColor(head_led, BLACK)
            strip.show()
        elif type(head_led) is tuple:
            # Multiple LEDS to turn off at the same time
            for hl in head_led:
                strip.setPixelColor(hl, BLACK)
                strip.show()
        else:
            print("Invalid type for head_led %s" % repr(type(head_led)))
            sys.exit(1)
        time.sleep(wait_ms/1000.0)
    # Above doesn't updated caller's hold_leds, so return updated list
    return hold_leds

def headTieOn(strip, baseLED, wait_ms=100):   #Eyes, node and tie on
    for x in NOSE:
        strip.setPixelColor(baseLED+x, ORANGE)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    for x in EYES:
        strip.setPixelColor(baseLED+x, BLUE)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    for x in TIE:
        strip.setPixelColor(baseLED+x, cheercolour)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    return

def spin(strip, baseLED):   #Clockwise
    for i in ARMS:
        strip.setPixelColor(baseLED+i, BLACK)
        strip.show()
    for n in range(10):
        for i in ARMS:
            strip.setPixelColor(baseLED+i, WHITE)
            strip.show()
            time.sleep(0.07)
            strip.setPixelColor(baseLED+i, BLACK)
            strip.show()
    for i in ARMS:
        strip.setPixelColor(baseLED+i, WHITE)
        strip.show()
    time.sleep(0.3)
    return

def spin2(strip, baseLED):   # Counter Clockwise
    for i in ARMS:
        strip.setPixelColor(baseLED+i, BLACK)
        strip.show()
    for n in range(10):
        for i in ARMS2:
            strip.setPixelColor(baseLED+i, WHITE)
            strip.show()
            time.sleep(0.07)
            strip.setPixelColor(baseLED+i, BLACK)
            strip.show()
    for i in ARMS2:
        strip.setPixelColor(baseLED+i, WHITE)
        strip.show()
    time.sleep(0.3)
    return

def wink(strip, baseLED):
    for  n in range(4):
        strip.setPixelColor(baseLED+10, BLACK)
        strip.show()
        time.sleep(0.2)
        strip.setPixelColor(baseLED+10, BLUE)
        strip.show()
        time.sleep(1.0)
    return

def wink2(strip, baseLED):
    for  n in range(4):
        strip.setPixelColor(baseLED+11, BLACK)
        strip.show()
        time.sleep(0.2)
        strip.setPixelColor(baseLED+11, BLUE)
        strip.show()
        time.sleep(1.0)
    return

def upDown(strip, baseLED):                  # Up and Down
    for n in range(1):
        for x in ((0, 3, 6), (1, 4, 7), (2, 5, 8), (9,), (11, 10)):
            for i in x:
                strip.setPixelColor(baseLED+i, BLACK)
                strip.show()
            time.sleep(0.2)
            for i in x:
                strip.setPixelColor(baseLED+i, LEDCOLORS[i])
                strip.show()
            time.sleep(0.2)
        for x in ((11, 10), (9,), (2, 5, 8), (1, 4, 7), (0, 3, 6)):
            for i in x:
                strip.setPixelColor(baseLED+i, BLACK)
                strip.show()
            time.sleep(0.2)
            for i in x:
                strip.setPixelColor(baseLED+i, LEDCOLORS[i])
                strip.show()
            time.sleep(0.2)
        time.sleep(0.5)
    return

def wobble(strip, baseLED):                  # Side to side
    for n in range(6):
        for i in ARML:
            strip.setPixelColor(baseLED+i, BLACK)
        strip.show()
        time.sleep(0.1)
        for i in ARML:
            strip.setPixelColor(baseLED+i, WHITE)
        strip.show()
        time.sleep(0.1)
        time.sleep(0.2)
        for i in ARMR:
            strip.setPixelColor(baseLED+i, BLACK)
        strip.show()
        time.sleep(0.1)
        for i in ARMR:
            strip.setPixelColor(baseLED+i, WHITE)
        strip.show()
        time.sleep(0.1)
        time.sleep(0.2)
    return

def allOn(strip, baseLED, wait_ms=100):
    for x in ARMS:
        strip.setPixelColor(baseLED+x, WHITE)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    for x in TIE:
        strip.setPixelColor(baseLED+x, cheercolour)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    for x in NOSE:
        strip.setPixelColor(baseLED+x, ORANGE)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    for x in EYES:
        strip.setPixelColor(baseLED+x, BLUE)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def allOff(strip, baseLED, wait_ms=100):
    for x in range(LED_COUNT):
        strip.setPixelColor(baseLED+x, BLACK)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def colorWipe(strip, baseLED, color, wait_ms=40):
    """Wipe color across display a pixel at a time."""
    for i in range(0, LED_COUNT):
        strip.setPixelColor(baseLED+i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChase(strip, baseLED, color, wait_ms=50, iterations=8):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, LED_COUNT, 3):
                strip.setPixelColor(baseLED+i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, LED_COUNT, 3):
                strip.setPixelColor(baseLED+i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, baseLED, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(LED_COUNT):
            strip.setPixelColor(baseLED+i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbowCycle(strip, baseLED, wait_ms=3, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(LED_COUNT):
            strip.setPixelColor(baseLED+i, wheel(
                (int(i * 256 / LED_COUNT) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChaseRainbow(strip, baseLED, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, LED_COUNT, 3):
                strip.setPixelColor(baseLED+i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, LED_COUNT, 3):
                strip.setPixelColor(baseLED+i + q, 0)

def runTheaterChase(strip, baseLED):
    theaterChase(strip, baseLED, Color(127, 127, 127))  # White theater chase
    theaterChase(strip, baseLED, Color(127, 0, 0))  # Red theater chase
    theaterChase(strip, baseLED, Color(0, 0, 127))  # Blue theater chase
    theaterChase(strip, baseLED, cheercolour)       # Cheerlights theater chase

def runColorWipe(strip, baseLED):
    for n in range(3):
        colorWipe(strip, baseLED, Color(255, 0, 0))  # Red wipe
        colorWipe(strip, baseLED, Color(0, 255, 0))  # Blue wipe
        colorWipe(strip, baseLED, Color(0, 0, 255))  # Green wipe
        colorWipe(strip, baseLED, cheercolour)       # Cheerlights wipe

def runRainbows(strip, baseLED):
    rainbow(strip, baseLED)
    rainbowCycle(strip, baseLED)

def all_snowmen_arms(strip, wait_ms=30):
    global cheercolour
    # Set up list for the leds to be held on for somecycles
    hold_leds = []
    # Max size of that list
    hold_max = 2 * args.m
    for snowman in range(args.m):
        baseLED = LED_COUNT*snowman
        for x in ARMS:
            strip.setPixelColor(baseLED+x, cheercolour)
            strip.show()
            # Add this LED to the list of ones to be turned off after a delay
            hold_leds_add(hold_leds, baseLED, x)
            time.sleep(wait_ms / 1000.0)
            # Turn off LEDs after a hold_max*wait_ms delay
            hold_leds = hold_leds_release(hold_leds, hold_max, strip, wait_ms)
    # Drain remaining LEDs, if any
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)

    for snowman in range(args.m-1, -1, -1):
        baseLED = LED_COUNT*snowman
        for x in ARMS2:
            strip.setPixelColor(baseLED+x, cheercolour)
            strip.show()
            # Add this LED to the list of ones to be turned off after a delay
            hold_leds_add(hold_leds, baseLED, x)
            time.sleep(wait_ms / 1000.0)
            # Turn off LEDs after a hold_max*wait_ms delay
            hold_leds = hold_leds_release(hold_leds, hold_max, strip, wait_ms)
    # Drain remaining LEDs, if any
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)

def next_color_loop(i):
    i += 1
    if i >= len(COLOR_LOOP):
        i = 0
    return(i, COLOR_LOOP[i])

def show_vertical(strip, baseLED, vcolor, LEDs, hold_leds, hold_max, wait_ms=75):
    if args.e:
        vcolid = cheercolour
    else:
        vcolor, vcolid = next_color_loop(vcolor)
    for x in LEDs:
        strip.setPixelColor(baseLED+x, vcolid)
    strip.show()
    hold_leds_add(hold_leds, baseLED, LEDs)

    time.sleep(wait_ms / 1000.0)

    hold_leds = hold_leds_release(hold_leds, hold_max, strip, wait_ms)
    return vcolor, hold_leds

def all_snowmen_verticals(strip, wait_ms=100):
    vcolor = 0
    hold_leds = []
    hold_max = args.m
    for snowman in range(args.m):
        baseLED = LED_COUNT*snowman
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (0, 1), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (2, 11), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (3, 4, 5, 9), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (8, 10), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (6, 7), hold_leds, hold_max)
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)
    for snowman in range(args.m-1, -1, -1):
        baseLED = LED_COUNT*snowman
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (6, 7), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (8, 10), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (3, 4, 5, 9), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (2, 11), hold_leds, hold_max)
        vcolor, hold_leds = show_vertical(strip, baseLED, vcolor, (0, 1), hold_leds, hold_max)
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)

def all_snowmen_horizontals(strip, wait_ms=75):
    # Light horizontal rows across all snowmen at once
    vcolor = 0
    hold_leds = []
    hold_max = 2
    for row in (11, 10), (9,), (2, 5, 8), (1, 4, 7), (0, 3, 6):
        if args.e:
            vcolid = cheercolour
        else:
            vcolor, vcolid = next_color_loop(vcolor)
        # Place to store the row across all snowmen
        wholerow = ()
        for snowman in range(args.m):
            baseLED = LED_COUNT*snowman
            for x in row:
                strip.setPixelColor(baseLED+x, vcolid)
            strip.show()
            wholerow += tuple([x+baseLED for x in row])
        # Set baseLED parameter to 0, as we've already added the relevant baseLEDs
        hold_leds_add(hold_leds, 0, wholerow)
        time.sleep(wait_ms / 1000.0)
        hold_leds = hold_leds_release(hold_leds, hold_max, strip, wait_ms)
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)
    time.sleep(wait_ms / 1000.0)

    for row in (0, 3, 6), (1, 4, 7), (2, 5, 8), (9,), (11, 10):
        if args.e:
            vcolid = cheercolour
        else:
            vcolor, vcolid = next_color_loop(vcolor)
        wholerow = ()
        for snowman in range(args.m):
            baseLED = LED_COUNT*snowman
            for x in row:
                strip.setPixelColor(baseLED+x, vcolid)
            strip.show()
            wholerow += tuple([x+baseLED for x in row])
        # Set baseLED parameter to 0, as we've already added the relevant baseLEDs
        hold_leds_add(hold_leds, 0, wholerow)
        time.sleep(wait_ms / 1000.0)
        hold_leds = hold_leds_release(hold_leds, hold_max, strip, wait_ms)
    hold_leds = hold_leds_release(hold_leds, 0, strip, wait_ms)
    time.sleep(wait_ms / 1000.0)

# Snowmen in Sync patterns
def all_snowmen_run(strip, wait_ms=100):
    if lights_on(on_off_times):
        # Start at the first snowman, run lights along right arm then left arm,
        # then next one, to end, then loop back
        # First turn all leds off
        for snowman in range(args.m):
            allOff(strip, LED_COUNT*snowman, wait_ms=0)

        for n in range(2):
            all_snowmen_arms(strip)
        for n in range(1):
            all_snowmen_verticals(strip)
        for n in range(3):
            all_snowmen_horizontals(strip)
        time.sleep(1.0)

# Set up configuraiton for on-off times

def read_config():
    # Return start and stop times, in pairs
    if args.f:
        # Force to run all day
        t0 = 3600*0 + 60*0 + 1
        t1 = 3600*23 + 60*59 + 59
    else:
        # Read config file, when coded!
        # Default is 8am to 10pm
        t0 = 3600*8 + 60*0 + 0
        t1 = 3600*22 + 60*0 + 0
    return [(t0, t1)]
    # if you want to return mutliple periods, it would look like:
    # return [(t0, t1), (t2, t3)]


def lights_on(onofftimes):
    # Return True if lights are supposed to be on
    # onofftimes is list of 'HH:MM' tuples - on if between 2 times of a tuple
    # Convert times to number of seconds
    now = datetime.datetime.now()
    nowt = 3600*now.hour + 60*now.minute + now.second
    for t0, t1 in onofftimes:
        #if nowt < t0:
        #    # Start time is past current time - give up
        #    # Assumes times in roder! - do not do for now
        #    break
        if nowt >= t0 and nowt < t1:
            return True
    return False

def time_snowman(strip):
    baseLED = 0 # Just do this on the first snowman

    b = time.perf_counter(); headTieOn(strip, baseLED, wait_ms=0); print("%5.2f %s" % (time.perf_counter()-b, "headTieOn"))
    b = time.perf_counter(); spin(strip, baseLED);                 print("%5.2f %s" % (time.perf_counter()-b, "spin"))
    b = time.perf_counter(); spin2(strip, baseLED);                print("%5.2f %s" % (time.perf_counter()-b, "spin2"))
    b = time.perf_counter(); allOn(strip, baseLED, wait_ms=0);     print("%5.2f %s" % (time.perf_counter()-b, "allOn"))
    b = time.perf_counter(); wink(strip, baseLED);                 print("%5.2f %s" % (time.perf_counter()-b, "wink"))
    b = time.perf_counter(); wink2(strip, baseLED);                print("%5.2f %s" % (time.perf_counter()-b, "wink2"))
    b = time.perf_counter(); wobble(strip, baseLED);               print("%5.2f %s" % (time.perf_counter()-b, "wobble"))
    b = time.perf_counter(); upDown(strip, baseLED);               print("%5.2f %s" % (time.perf_counter()-b, "upDown"))
    b = time.perf_counter(); runTheaterChase(strip, baseLED);      print("%5.2f %s" % (time.perf_counter()-b, "runTheaterChase"))
    b = time.perf_counter(); runColorWipe(strip, baseLED);         print("%5.2f %s" % (time.perf_counter()-b, "runColorWipe"))
    b = time.perf_counter(); rainbow(strip, baseLED);              print("%5.2f %s" % (time.perf_counter()-b, "rainbow"))
    b = time.perf_counter(); rainbowCycle(strip, baseLED);         print("%5.2f %s" % (time.perf_counter()-b, "rainbowCycle"))
    allOff(strip, baseLED, wait_ms=0)

def run_snowman(snowman,strip):
    global insync, idlemen

    if verbose:
        print("Snowman %d start" % (snowman))
    # Run nth snowman in chain
    baseLED = snowman * LED_COUNT

    Current_State  = 0
    Previous_State = 0

    # === stop lights on this snowman and exit ===
    if args.o:
        allOff(strip, baseLED, wait_ms=0)
        return

    # ==== Initial display begins ====
    if not args.q:
        allOn(strip, baseLED)
        wobble(strip, baseLED)
        upDown(strip, baseLED)
        upDown(strip, baseLED)
        wink(strip, baseLED)
        wink2(strip, baseLED)
        allOff(strip, baseLED)
        headTieOn(strip, baseLED)
        spin(strip, baseLED)
        spin2(strip, baseLED)
        allOff(strip, baseLED)
        time.sleep(1.0)
        allOn(strip, baseLED, wait_ms=0.0)
        time.sleep(1.0)
        allOff(strip, baseLED, wait_ms=0.0)


    try:
        while True:
          try:
            # If We are in the Synchronized state, tell main thread that we are ready
            # and just loop unti the insync flag is turned off
            if insync:
                idlemen += 1
                while insync:
                    time.sleep(0.2)


            # We are not in a synchronised state - show lights (if it's the right time)
            if lights_on(on_off_times):

                # we are in a display time - show lights
                if args.p:
                    Current_State = GPIO.input(sw)
                else:
                    # No PIR - just toggle to pause between displays
                    if Current_State == 0:
                        Current_State = args.n
                    else:
                        Current_State -= 1

                if Current_State>=1:
                    # PIR is triggered
                    if Previous_State==0:
                        if verbose:
                            print("  Motion detected!")
                        allOn(strip, baseLED)
                        Previous_State=1
                    if args.p:
                        # PIR-driven - always display a pattern
                        n = random.randint(0,9)
                    else:
                        # Fixed - only display 75% of time
                        n = random.randint(0,15)
                    if n == 0 and show_a:
                        headTieOn(strip, baseLED, wait_ms=0)
                        spin(strip, baseLED)
                    if n == 1 and show_a:
                        headTieOn(strip, baseLED, wait_ms=0)
                        spin2(strip, baseLED)
                    if n == 2 and show_a:
                        allOn(strip, baseLED, wait_ms=0)
                        wink(strip, baseLED)
                    if n == 3 and show_a:
                        allOn(strip, baseLED, wait_ms=0)
                        wink2(strip, baseLED)
                    if n == 4 and show_a:
                        headTieOn(strip, baseLED, wait_ms=0)
                        wobble(strip, baseLED)
                    if n == 5 and show_a:
                        upDown(strip, baseLED)
                    if n == 6 and show_t:
                        runTheaterChase(strip, baseLED)
                    if n == 7 and show_w:
                        runColorWipe(strip, baseLED)
                    if n == 8 and show_r:
                        rainbow(strip, baseLED)
                    if n == 9 and show_r:
                        rainbowCycle(strip, baseLED)
                    if n >  9:
                        allOff(strip, baseLED)

                elif Current_State==0:
                    if Previous_State==1:
                        # PIR has returned to ready state
                        if verbose:
                            print("  Idle")
                        Previous_State=0
                        allOff(strip, baseLED)
                    # Sleep between displays
                    time.sleep(args.s)
            else:
                # We are in "off" time - if lights on, turn them off,
                # if not on, leve them alone
                if Previous_State==1:
                    # Lights were on - turn them off
                    if verbose:
                        print("  Dark")
                    Previous_State=0
                    allOff(strip, baseLED)
                    time.sleep(30.0)
          except KeyboardInterrupt:
            if verbose:
                print("Keyboard interrupt in thread for snowman %d" % snowman)
            break


    except KeyboardInterrupt:
        # Reset GPIO settings
        if args.p:
            GPIO.cleanup()
        allOff(strip, baseLED)
        return

if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    parser.add_argument('-b', '--brightness', action='store', dest='b', default=LED_BRIGHTNESS, type=int, help='Set the brightness 0-255 default %(default)s')
    #parser.add_argument('-a', '--all', action='store_true', dest='a', help='Run All Demos')
    parser.add_argument('-a', '--action', action='store_true', dest='a', help='Only Run old-style Action demos')
    parser.add_argument('-w', '--wipe', action='store_true', dest='w', help='Only Run Wipe Demos')
    parser.add_argument('-t', '--theater', action='store_true', dest='t', help='Only Run Theater Chase Demos')
    parser.add_argument('-r', '--rainbow', action='store_true', dest='r', help='Only Run Rainbow Demos')
    parser.add_argument('-q', '--quietdemo', action='store_true', dest='q', help='Suppress demo startup sequence')
    parser.add_argument('--off', action='store_true', dest='o', help='Just turn lights off and exit')
    parser.add_argument('-l', '--lcount', action='store', dest='l', type=int, default=40, help='Approximate Seconds between all-snowmen displays, default %(default)s')
    parser.add_argument('-s', '--sleep', action='store', dest='s', type=float, default=5.0, help='Seconds between displays, default %(default)s')
    parser.add_argument('-n', '--numdisp', action='store', dest='n', type=int, default=1, help='Number of displays per sleep, default %(default)s')
    parser.add_argument('-m', '--men', action='store', dest='m', type=int, default=1, help='Number of snowmen, default %(default)s')
    parser.add_argument('-f', '--forever', action='store_true', dest='f', help='Run all day, ignore time limits')
    parser.add_argument('-p', '--pir', action='store_true', dest='p', help='PIR is present')
    parser.add_argument('-e', '--cheerlights', action='store_true', dest='e', help='Cheerlights connection via MQTT')
    parser.add_argument('-v', '--verbose', action='store_true', dest='v', help='Verbose logging')
    parser.add_argument('--time', action='store_true', dest='time', help='Just time each display method')
    args = parser.parse_args()

    # Set flags for things to display
    show_a = args.a
    show_t = args.t
    show_r = args.r
    show_w = args.w
    verbose = args.v
    # if none specified, set all
    if not (args.a or args.t or args.r or args.w):
        show_a = show_t = show_r = show_w = True

    # get times to turn the display on or off
    on_off_times = read_config()

    # ==== Set up PIR ====
    if args.p:
        import RPi.GPIO as GPIO

        # Tell GPIO library to use GPIO references
        GPIO.setmode(GPIO.BCM)
        sw = PIR_SENSE
        GPIO.setup(sw,GPIO.IN)

        try:
            if verbose:
                print("Waiting for PIR to settle ...")

            # Loop until PIR output is 0
            # Time out after a second
            c = 0
            while c<10 and GPIO.input(sw)==1:
                c += 1
                time.sleep(0.1)

            if verbose:
                print("  Ready")

        except KeyboardInterrupt:
           # Interrupt while starting
            # Reset GPIO settings
            GPIO.cleanup()
            sys.exit(0)

    # ==== Set up MQTT connection to cheerlights ====
    if args.e:
        import paho.mqtt.client as paho

        # Channels "color", "colour" or "hex"
        mytopic = "hex"

        def on_message(client, userdata, message):
            # Called if a message is received - set the color from the message text
            global state, cheercolour
            try:
                cheermsg = message.payload.decode("utf-8")
                if verbose:
                    print("Cheercolour = %s" % cheermsg)
                cheercolour = int(cheermsg[1:], 16)
                if verbose:
                    print("Cheercolour = 0x%x" % cheercolour)
            except:
                cheercolour = GREEN

            #if verbose:
            #    print("%s Topic %s, mid %d, Payload: %s" %
            #          (datenow(), message.topic, message.mid, cheermsg))


        def on_connect(client, userdata, flags, rc):
            # Called if a connection is made
            global state
            if verbose:
                print("%s Connection returned %d: %s" %
                      (datenow(), rc, paho.connack_string(rc)))
            state = "connected"

        cheer = paho.Client()

        # Set up the "message" handler
        cheer.on_message = on_message
        cheer.on_connect = on_connect

        # Open the connection to the Cherlights server
        rc = cheer.connect('mqtt.cheerlights.com', 1883, 60)
        if rc != 0:
            print("%s Error connecting to server %d: %s" %
                  (datenow(), rc, paho.connack_string(rc)))
            sys.exit(1)

        rc, mid = cheer.subscribe(mytopic, 0)
        if verbose:
            print("Return code from subscribe to %s = %d" % (mytopic, rc))
        cheer.loop_start()


    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(args.m*LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, args.b, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    # If timing the individual patterns ,do that and exit
    if args.time:
        time_snowman(strip)
        if args.p:
            GPIO.cleanup()
        sys.exit(0)

    # === Main Loop ===
    threadlist = []
    try:
        # Start the individual snowmen
        for snowman in range(args.m):
            x = threading.Thread(target=run_snowman, args=(snowman,strip,))
            #x.daemon = True
            x.start()
            threadlist.append(x)
            time.sleep(0.1)

        # All snowmen now doing their own thing. Now, periodically set a flag so that all
        # of them stop what they are doing, and a single thread controls all of them.
        # Then it switches back to individual snowmen for another period.
        # maxlcount is the approx number of seconds before we do synchronized display.
        maxlcount = args.l
        nummen = len(threadlist)
        while threading.active_count() > 1:
            lcount = 0
            while lcount < maxlcount:
                if threading.active_count() == 1:
                    break
                time.sleep(1)
                lcount += 1
            # Wait for all snowmen to go idle
            if verbose:
                print("Wait for all snowmen to be idle")
            idlemen = 0
            insync = True
            while idlemen < nummen:
                if verbose:
                    print("Wait for insync, %d idle of %d" % (idlemen, nummen))
                if threading.active_count() == 1:
                    break
                time.sleep(1)

            # All idle and still running - do some funky stuff
            if threading.active_count() > 1:
                if verbose:
                    print("All snowmen idle - do centralised display")
                all_snowmen_run(strip)

            # All done - revert to out-of-sync
            idlemen = 0
            insync = False
            if verbose:
                print("Out of sync")


    except KeyboardInterrupt:
        # Don't do anything with KbdInt, just fall off try/catch and do the "finally" caluse to shut down
        pass
    finally:
        pass
        #for x in threadlist:
        #    x.stop()

