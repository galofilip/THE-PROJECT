# B33 Pi 4 Firmware

Python firmware for the Raspberry Pi 4 — the main B33 field device.

## Wiring

```
Component   Pi 4 Pin       GPIO
---------   ---------      ----
OLED SDA    Pin 3          GPIO 2
OLED SCL    Pin 5          GPIO 3
OLED VCC    Pin 1          3.3V
OLED GND    Pin 6          GND

BTN DOWN    Pin 11  +  GND    GPIO 17
BTN ENTER   Pin 13  +  GND    GPIO 27

Pico 2WH    Any USB-A port    (USB serial /dev/ttyACM0)
```

Button wiring: one leg to the GPIO pin, the other leg to any GND pin.
No resistors needed — internal pull-ups are enabled in software.

## Display Driver

Check the chip name printed on the back of your OLED board:
- **SSD1306** → no change needed (default)
- **SH1106** → open `display.py` and change line 6 to:
  ```python
  _DRIVER = sh1106
  ```

## OS Setup

1. Flash **Raspberry Pi OS Lite (64-bit)** onto the micro SD card using Raspberry Pi Imager.
   - Enable SSH in the imager settings if you want headless access.
2. Boot the Pi 4, connect to WiFi via `sudo raspi-config` → System → Wireless LAN.
3. Enable I2C: `sudo raspi-config` → Interface Options → I2C → Yes.

## Install Dependencies

```bash
sudo apt update && sudo apt install -y python3-pip
cd /path/to/repo/pi4
pip3 install -r requirements.txt
```

## Configure Settings

Create `/boot/b33_settings.json`:

```json
{
  "server_url": "https://the-project-gukh.onrender.com",
  "api_key": "your-api-key-here",
  "poll_interval": 30,
  "scan_timeout": 0.5
}
```

This file is gitignored — never commit it.

## Run

```bash
cd /path/to/repo/pi4
python3 main.py
```

To auto-start on boot, add to `/etc/rc.local` before `exit 0`:

```bash
cd /home/pi/b33/pi4 && python3 main.py &
```

## File Overview

| File | Role |
|------|------|
| `main.py` | Entry point, asyncio event loop, menu |
| `config.py` | Load `/boot/b33_settings.json` |
| `display.py` | SSD1306/SH1106 OLED wrapper |
| `buttons.py` | GPIO button handler (DOWN=GPIO17, ENTER=GPIO27) |
| `wifi_manager.py` | WiFi status via nmcli |
| `api_client.py` | HTTP client for Go server |
| `scanner.py` | LAN host discovery, port scan, CVE lookup |
| `hid_controller.py` | Send HID commands to Pico over USB serial |
| `poller.py` | 30s background poll loop |
| `task_runner.py` | Execute tasks received from server |
| `requirements.txt` | pip dependencies |
