# Pi Snowman RGB on Raspberry Pi

This code displays on the Ryanteck RGB Snowman running on a Raspberry Pi
(any one - a Pi Zero is fine), and is able to power multiple snowman
(tested up to 5, as that's all I have!).
The Snowman itself just plugs onto the GPIO pins, but soldering is
required to have multiple snowmen.

The code uses Python3, but this will be installed if you have a recent OS.

## Usage

    usage: sudo snowrgb.py [-h] [-c] [-b B] [-a] [-w] [-t] [-r] [-q] [--off]
                        [-l L] [-s S] [-n N] [-m M] [-p] [-v] [--time]
    optional arguments:
      -h, --help            show this help message and exit
      -c, --clear           clear the display on exit
      -b B, --brightness B  Set the brightness 0-255, default 20
      -a, --action          Only Run old-style Action demos
      -w, --wipe            Only Run Wipe Demos
      -t, --theater         Only Run Theater Chase Demos
      -r, --rainbow         Only Run Rainbow Demos
      -q, --quietdemo       Suppress demo startup sequence
      --off                 Just turn lights off and exit
      -l L, --lcount L      Approximate Seconds between all-snowmen displays,
                            default 40
      -s S, --sleep S       Seconds between displays, default 5.0
      -n N, --numdisp N     Number of displays per sleep, default 1
      -m M, --men M         Number of snowmen, default 1
      -f, --forever         Ignore any time-limits - late-night testing!
      -p, --pir             PIR is present
      -e, --cheerlights     Display some LEDs in cheerlights.com colour
      -v, --verbose         Verbose logging
      --time                Just time each display method

## Normal running

The code starts a thread for each snowman attached, and they run separately,
displaying a number of patterns in a random order.

The code normally starts with a "demo" period, where the snowman displays
most of the available patterns for a few seconds. The "-q" option omits this.

If you attach multiple snowmen (see below), set the "-m" option.

After a confgurable time (the "-l" option, default 40 seconds), the indvidual
snowman stop displaying their own patterns, and a co-ordinated pattern runs
across all of the snowmen (even if there is only one of them!).

When the code stops, it may leave some LEDs lit. Calling the program with
the "-c" option may avoid this.

You may need to press Ctrl-C twice to get the code to stop.

If you just give the "--off" option, turn all LEDs off and exit.

## Display time periods

The system will normally impose time limits on display (so that it doesn't
run all night, for example). The  "-f" option overrides the limites and runs
all of the time (good for late-night testing).

At the moment the times are in code, so will need an edit to change them.

Look for the `def read_config():` function, at about line 400.
You will see lines setting `t0` and `t1` - these are the start and
end times for the "on" period for the lights. The times are in seconds
from midnight, and are shown as calculations frmo a number of hours,
minutes and seconds. The default is from 8AM to 10PM (08:00 to 22:00).
There is a comment showing how you can specify multiple periods -
it shows 2, but just add more comma-separated 2-value tuples if needed.

If you feel brave, you can code an actual configuration file, and make
a Pull Request :-)

## Requirements 

The code assumes that the Snowman is set up and working (e.g. that the
`rpi_ws281x` driver has been installed). See xxx (was snowpi.xyz) for details.

The SnowpiRGB is plugged into pins 2, 4, 6, 8, 10, 12 as usual.

You can attach a PIR (Passive InfraRed) sensor, so that the snowman/men only
lights up when someone walks by. Just add the "-p" flag. The PIR's 5V wire
is soldered to the back of SnowPiRGB (either the GPIO pin 2, or the 5v
connection next to the "data in" pad on the side of the snowman). Ground is
attached to GPIO pin 34, the the signal wire to pin 36 (GPIO16).  See
https://maker.pro/raspberry-pi/tutorial/how-to-interface-a-pir-motion-sensor-with-raspberry-pi-gpio
for more details.

If you don't want PIR control, just don't use the "-p" flag, and the snowman will run ocntinuously.

## Running the code

### Manual

Log in to the Pi, go to the directory with the snowrgb, and run this,
with whichever options you want:

    sudo ./snowrgb.py -c

### Simple automation

You can add a call to crontab so that the code starts on boot.
This will probably work, but it may try to start before the Pi is really
ready for it, and if the code crashes it won't restart.

If this sounds OK, edit root's crontab with `sudo crontab -e` and add the
following line, with any options that you want

    @reboot python3 /home/pi/snowrgb.py -c -q -m 3 -n 3 -s 2

### systemctl automation

Better is to use systemctl (asusming that your Pi uses it - recent Raspbian
and Raspberry PI OS versions will). This will start the snowman when the
system is ready, and will restart it if it fails.

Add the following code to `/etc/systemd/system/rgbsnow.service` (if you use
a different filename, change the "start" and "enable" commands below):

    [Unit]
    Description=RGB Snowman service
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/pi/snowrgb.py -c -q -m 5 -s 2 -n 3
    Restart=on-failure
    Type=simple

    [Install]
    WantedBy=multi-user.target

The run the following commands

    sudo systemctl daemon-reload
    sudo systemctl start rgbsnow
    sudo systemctl enable rgbsnow

## Multiple snowmen

One of the main features of this code is that it supports multiple snowmen,
driven by a single Raspberry Pi.

To wire up the snowmen:

* Start with the snowman which will be attached to Pi's GPIO pins.
Don't actually have it plugged in to the Pi for this process,
as you may harm it while soldering.

* Look at the back of the snowman. On the left-hand side of the body you
will see pads labelled GND, DOUT and 5v. On the right you have GND, DIN
and 5v. GND and 5v are Ground and 5 volts. DOUT is a data-out line
(which takes the control signals being applied to the snowman,
and feeds them out to some other device).
DIN takes those same signals and runs this Snowman from them.

* Starting on the left-hand side of the first Snowman, connect GND, DOUT
and 5v with thin wires to GND, DIN and 5v on the right-hand side of the
next snowman in the sequence. Connect GND on the first snowman to GND on
the second, DOUT on the first to DIN on the second and 5v on the first to
5v on the second.

* If you have more snowmen, connect the GND, DOUT and 5v of the second
snowman to GND, DIN and 5v of the 3rd snowman, and so on in a daisy chain.
The final snowman will have wires attached to the DIN side, but nothing
on the DOUT side.

* Finally, use the "-m" option to specify how many snowmen you have.

## Chherlights connection

The code will display the current global cheerlights colour if you
use the "-e" option. It sets up an MQTT connection so that changes to the
colour are displayed immediately (rather than having to poll for the colour).

For details of the #cheerlights phenomenon, see cheerlights.com.

