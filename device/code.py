import re

import usb_hid
import usb_cdc
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_macropad import MacroPad

class AppExit(Exception):
    pass

class App():
    def __init__(self, macropad: MacroPad):
        self.macropad = macropad

    def handle(self):
        if self.macropad.encoder_switch:
            raise AppExit()

class Numpad(App):
    key_assignment = {
        0:  Keycode.KEYPAD_SEVEN,
        1:  Keycode.KEYPAD_EIGHT,
        2:  Keycode.KEYPAD_NINE,
        3:  Keycode.KEYPAD_FOUR,
        4:  Keycode.KEYPAD_FIVE,
        5:  Keycode.KEYPAD_SIX,
        6:  Keycode.KEYPAD_ONE,
        7:  Keycode.KEYPAD_TWO,
        8:  Keycode.KEYPAD_THREE,
        9:  Keycode.KEYPAD_ENTER,
        10: Keycode.KEYPAD_ZERO,
        11: Keycode.KEYPAD_NUMLOCK,
    }

    def __init__(self, macropad: MacroPad):
        super().__init__(macropad)
        self.text_lines = self.macropad.display_text()
        for line in range(3):
            base = (2 - line) * 3 + 1
            a, b, c = base, base + 1, base + 2
            text = "{:5} {:5} {:5}".format(a, b, c)
            self.text_lines[line].text = text

        text = "  {:5} {:3}  {:5}".format("Enter", 0, "NUMLOCK")
        self.text_lines[3].text = text
        self.text_lines.show()

        # enable NUM_LOCK initially
        if not kbd.led_on(kbd.LED_NUM_LOCK):
            kbd.press(Keycode.KEYPAD_NUMLOCK)
            kbd.release(Keycode.KEYPAD_NUMLOCK)

    def handle(self):
        super().handle()
        event = self.macropad.keys.events.get()

        while event is not None:
            if event.pressed:
                kbd.press(self.key_assignment[event.key_number])
            else:
                kbd.release(self.key_assignment[event.key_number])
            event = self.macropad.keys.events.get()

        if kbd.led_on(kbd.LED_NUM_LOCK):
            self.macropad.pixels[11] = 0xFF00000
        else:
            self.macropad.pixels[11] = 0x0



class LED_handling():
    COLORS = {
        'RED': 0xFF0000,
        'GREEN': 0x00FF00,
        'BLUE': 0x0000FF,
        'OFF': 0x00000,
    }

    def __init__(self, macropad: MacroPad) -> None:
        regex = r'\|\|;1>LED (\S+) (\S+)'
        self.re = re.compile(regex)
        self.buffered_data = ""
        self.macropad = macropad

    def _set_color(self, led: str, color: str):
        if color in self.COLORS:
            color = self.COLORS[color]
        else:
            color = int(color, 0)
        if led is 'ALL':
            for i in range(12):
                self.macropad.pixels[i] = color
        else:
            self.macropad.pixels[int(led, 0)] = color

    def handle(self):
        if usb_cdc.console.in_waiting:
            data = usb_cdc.console.read(usb_cdc.console.in_waiting)
            self.buffered_data += data.decode()
            if ('\n' in self.buffered_data) or ('\r' in self.buffered_data):
                match = self.re.search(self.buffered_data)
                if match:
                    led = match.group(1)
                    color = match.group(2)
                    self._set_color(led, color)
                else:
                    print("buuh:" , self.buffered_data)

                self.buffered_data = ""

# Set up a keyboard device.
kbd = Keyboard(usb_hid.devices)
macropad = MacroPad()
app = None
default_app = Numpad

led_stuff = LED_handling(macropad)


while True:
    if not app:
        print("App set to", default_app)
        app = Numpad(macropad)

    try:
        app.handle()
    except AppExit:
        app = None

    led_stuff.handle()