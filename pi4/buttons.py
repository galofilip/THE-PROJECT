import asyncio
from gpiozero import Button

_PIN_DOWN = 17
_PIN_ENTER = 27
_DEBOUNCE_S = 0.05

_btn_down = None
_btn_enter = None


def init():
    global _btn_down, _btn_enter
    _btn_down = Button(_PIN_DOWN, pull_up=True, bounce_time=_DEBOUNCE_S)
    _btn_enter = Button(_PIN_ENTER, pull_up=True, bounce_time=_DEBOUNCE_S)


async def read_event():
    """Block until a button is pressed; return 'down' or 'enter'."""
    if _btn_down is None or _btn_enter is None:
        await asyncio.sleep(9999)
        return "enter"
    while True:
        if _btn_down.is_pressed:
            await asyncio.sleep(_DEBOUNCE_S)
            while _btn_down.is_pressed:
                await asyncio.sleep(0.01)
            return "down"
        if _btn_enter.is_pressed:
            await asyncio.sleep(_DEBOUNCE_S)
            while _btn_enter.is_pressed:
                await asyncio.sleep(0.01)
            return "enter"
        await asyncio.sleep(0.02)


async def wait_enter():
    """Block until any button is pressed."""
    await read_event()
