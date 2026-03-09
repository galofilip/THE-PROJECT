# B33 Pico 2WH Firmware

CircuitPython firmware for the Raspberry Pi Pico 2WH.
The Pico acts as a USB HID keyboard emulator, controlled by the Pi 4 over USB serial.

## Flashing CircuitPython

1. Download **CircuitPython 9.x** for Pico 2WH from https://circuitpython.org/board/raspberry_pi_pico2_w/
2. Hold BOOTSEL button on the Pico, plug into PC via USB — it mounts as a USB drive called `RPI-RP2`.
3. Drag the downloaded `.uf2` file onto the drive. Pico reboots as `CIRCUITPY`.

## Install Libraries

Download the **Adafruit CircuitPython Bundle 9.x** from https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases

Copy these into `CIRCUITPY/lib/`:
- `adafruit_hid/` (the whole folder)

## Copy Firmware Files

Copy these files to the root of `CIRCUITPY/`:
- `code.py`
- `hid_payload.py`

## How It Works

1. Pico boots and runs `code.py`, which prints `ready` on the USB serial port.
2. Pi 4 connects to the Pico's serial port (`/dev/ttyACM0`) via pyserial.
3. Pi 4 sends a JSON command: `{"os": "windows", "server_url": "...", "api_key": "..."}`.
4. Pico reads the command, executes the appropriate HID keyboard sequence, and responds with `{"status": "ok"}`.

## Testing

You can test the Pico without the Pi 4 by opening a serial terminal (e.g. Mu editor, or `screen /dev/ttyACM0 115200`) and typing the JSON command manually.

## Connecting to Pi 4

Plug the Pico into any USB-A port on the Pi 4. The Pi 4 firmware (`hid_controller.py`) will automatically detect it at `/dev/ttyACM0`.
