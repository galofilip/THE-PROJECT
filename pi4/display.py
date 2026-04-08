from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106
from PIL import Image, ImageDraw, ImageFont

# Change to sh1106 if your display board has that chip printed on the back.
_DRIVER = ssd1306

_WIDTH = 128
_HEIGHT = 64
_FONT = ImageFont.load_default()

_device = None


def init(driver=None):
    global _device, _DRIVER
    if driver is not None:
        _DRIVER = driver
    serial = i2c(port=1, address=0x3C)
    _device = _DRIVER(serial, width=_WIDTH, height=_HEIGHT)


def _blank():
    return Image.new("1", (_WIDTH, _HEIGHT), 0)


def show_text(lines):
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines[:5]):
        draw.text((0, i * 13), str(line), font=_FONT, fill=255)
    _device.display(img)


def show_menu(title, items, selected_idx):
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), title, font=_FONT, fill=255)
    draw.line((0, 11, _WIDTH, 11), fill=255)
    for i, item in enumerate(items[:4]):
        y = 14 + i * 12
        prefix = "> " if i == selected_idx else "  "
        draw.text((0, y), f"{prefix}{item}", font=_FONT, fill=255)
    _device.display(img)


def show_progress(label, current, total):
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), label, font=_FONT, fill=255)
    bar_w = _WIDTH - 4
    filled = int(bar_w * current / max(total, 1))
    draw.rectangle((2, 20, 2 + bar_w, 32), outline=255)
    if filled > 0:
        draw.rectangle((2, 20, 2 + filled, 32), fill=255)
    pct = int(100 * current / max(total, 1))
    draw.text((0, 38), f"{current}/{total}  ({pct}%)", font=_FONT, fill=255)
    _device.display(img)


def show_status(msg, detail=""):
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.text((0, 10), msg, font=_FONT, fill=255)
    if detail:
        draw.text((0, 28), detail[:21], font=_FONT, fill=255)
    _device.display(img)


def clear():
    if _device:
        _device.cleanup()
