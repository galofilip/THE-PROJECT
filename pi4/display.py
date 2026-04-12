import random
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106
from PIL import Image, ImageDraw, ImageFont

_DRIVER = sh1106
_WIDTH = 128
_HEIGHT = 64
_FONT = ImageFont.load_default()
_device = None

# Spinner frames
SPINNER = ["|", "/", "-", "\\"]

# Matrix rain character pool
MATRIX_CHARS = "0123456789ABCDEF!@#$<>?/\\"


def init(driver=None):
    global _device, _DRIVER
    if driver is not None:
        _DRIVER = driver
    serial = i2c(port=1, address=0x3C)
    _device = _DRIVER(serial, width=_WIDTH, height=_HEIGHT)


def _blank():
    return Image.new("1", (_WIDTH, _HEIGHT), 0)


# ── Core display functions ────────────────────────────────────────────────────

def show_text(lines):
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines[:5]):
        draw.text((0, i * 13), str(line), font=_FONT, fill=255)
    _device.display(img)


def show_typewriter(lines, char_count):
    """Show text with typewriter effect — only reveal first char_count chars."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    remaining = char_count
    for i, line in enumerate(lines):
        if remaining <= 0:
            break
        visible = str(line)[:remaining]
        draw.text((0, i * 13), visible, font=_FONT, fill=255)
        remaining -= len(str(line))
    _device.display(img)


def show_menu(title, items, selected_idx, status_line=""):
    """Menu with scrolling and optional status bar at bottom."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), title, font=_FONT, fill=255)
    draw.line((0, 11, _WIDTH, 11), fill=255)
    max_visible = 3 if status_line else 4
    # Scroll window: keep selected_idx visible
    scroll = max(0, selected_idx - max_visible + 1)
    visible = items[scroll:scroll + max_visible]
    for i, item in enumerate(visible):
        actual_idx = scroll + i
        y = 14 + i * 12
        prefix = "> " if actual_idx == selected_idx else "  "
        draw.text((0, y), f"{prefix}{item}", font=_FONT, fill=255)
    if status_line:
        draw.line((0, 54, _WIDTH, 54), fill=255)
        draw.text((0, 56), status_line[:21], font=_FONT, fill=255)
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
        draw.text((0, 28), str(detail)[:21], font=_FONT, fill=255)
    _device.display(img)


def show_notify(msg, detail=""):
    """Notification overlay — bordered box."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.rectangle((2, 10, _WIDTH - 2, 54), outline=255)
    draw.text((6, 16), msg, font=_FONT, fill=255)
    if detail:
        draw.text((6, 30), str(detail)[:18], font=_FONT, fill=255)
    _device.display(img)


# ── Animation helpers ─────────────────────────────────────────────────────────

def spinner_frame(label, frame_idx, detail=""):
    """One frame of a spinner animation."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    spin_char = SPINNER[frame_idx % 4]
    draw.text((0, 0), f"{spin_char} {label}", font=_FONT, fill=255)
    if detail:
        draw.text((0, 20), str(detail)[:21], font=_FONT, fill=255)
    _device.display(img)


def flash():
    """Flash screen white (call, then redraw your content)."""
    if not _device:
        return
    img = Image.new("1", (_WIDTH, _HEIGHT), 255)
    _device.display(img)


# ── Screensaver frames ────────────────────────────────────────────────────────

def show_matrix_frame(drops, chars):
    """Render one frame of matrix rain."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    col_w = 6
    row_h = 8
    rows = _HEIGHT // row_h  # 8

    for col_idx, drop_row in enumerate(drops):
        x = col_idx * col_w
        # Head of drop (brightest)
        if 0 <= drop_row < rows:
            draw.text((x, drop_row * row_h), chars[col_idx], font=_FONT, fill=255)
        # Tail — 2 rows above head
        for tail in range(1, 3):
            tail_row = drop_row - tail
            if 0 <= tail_row < rows:
                tail_char = chars[(col_idx + tail * 3) % len(chars)]
                draw.text((x, tail_row * row_h), tail_char, font=_FONT, fill=255)
    _device.display(img)


def show_bounce_frame(bx, by, text="B33"):
    """Render bouncing logo frame with border."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, _WIDTH - 1, _HEIGHT - 1), outline=255)
    draw.text((int(bx), int(by)), text, font=_FONT, fill=255)
    _device.display(img)


def show_glitch_frame(lines, glitch_level):
    """Text with random glitch chars injected."""
    if not _device:
        return
    img = _blank()
    draw = ImageDraw.Draw(img)
    glitch_chars = "!@#$%^&*|\\/<>?~"
    for i, line in enumerate(lines[:5]):
        glitched = ""
        for ch in str(line):
            if random.random() < glitch_level:
                glitched += random.choice(glitch_chars)
            else:
                glitched += ch
        draw.text((0, i * 13), glitched, font=_FONT, fill=255)
    _device.display(img)


def clear():
    if _device:
        _device.cleanup()
