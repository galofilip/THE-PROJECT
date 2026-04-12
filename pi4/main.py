import asyncio
import random
import sys

import config
import display
import buttons
import wifi_manager
import api_client as api_module
import scanner
import hid_controller
import poller
import task_runner

_MENU_ITEMS = ["Scan LAN", "Deploy HID", "Task Status", "Settings", "Screensaver"]
_selected = 0

# Global state for status bar
_server_ok = False
_last_scan_count = None  # None = never scanned
_ssid = ""
_local_ip = ""

_SCREENSAVER_TIMEOUT = 60  # seconds of inactivity before auto-screensaver


# ── Status bar ────────────────────────────────────────────────────────────────

def _status_line():
    wifi = (_ssid[:8] if _ssid else "NoWiFi")
    srv = "S:OK" if _server_ok else "S:OFF"
    hosts = f"H:{_last_scan_count}" if _last_scan_count is not None else ""
    parts = [wifi, srv]
    if hosts:
        parts.append(hosts)
    return " ".join(parts)[:21]


# ── Animation helpers ─────────────────────────────────────────────────────────

async def _spin(label, detail=""):
    """Spinner loop — cancel this task to stop it."""
    frame = 0
    while True:
        display.spinner_frame(label, frame, detail)
        frame += 1
        await asyncio.sleep(0.15)


async def _boot_animation():
    lines = ["B33 v1.0", "Init systems...", "Hacking planet"]
    total = sum(len(l) for l in lines)
    for i in range(total + 1):
        display.show_typewriter(lines, i)
        await asyncio.sleep(0.035)
    # Brief glitch effect at end
    for level in [0.3, 0.5, 0.2, 0.0]:
        display.show_glitch_frame(lines, level)
        await asyncio.sleep(0.07)
    await asyncio.sleep(0.2)


# ── Screensaver ───────────────────────────────────────────────────────────────

async def _any_button(timeout):
    """Wait for a button press with timeout. Returns True if pressed, False if timed out."""
    try:
        await asyncio.wait_for(buttons.read_event(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False


async def _matrix_rain(duration=20):
    """Returns True if exited by button press."""
    col_w = 6
    cols = display._WIDTH // col_w
    rows = display._HEIGHT // 8
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    chars = [random.choice(display.MATRIX_CHARS) for _ in range(cols)]
    loop = asyncio.get_running_loop()
    end = loop.time() + duration

    while loop.time() < end:
        if await _any_button(0.08):
            return True
        display.show_matrix_frame(drops, chars)
        for i in range(cols):
            drops[i] += 1
            if drops[i] > rows + 3:
                drops[i] = random.randint(-5, 0)
                chars[i] = random.choice(display.MATRIX_CHARS)
            if random.random() < 0.12:
                chars[i] = random.choice(display.MATRIX_CHARS)
    return False


async def _bounce_logo(duration=15):
    """Returns True if exited by button press."""
    x, y = 55.0, 28.0
    dx, dy = 1.5, 1.1
    text = "B33"
    text_w = len(text) * 6
    text_h = 8
    loop = asyncio.get_running_loop()
    end = loop.time() + duration

    while loop.time() < end:
        if await _any_button(0.05):
            return True
        display.show_bounce_frame(x, y, text)
        x += dx
        y += dy
        if x <= 2 or x >= display._WIDTH - text_w - 2:
            dx = -dx
        if y <= 2 or y >= display._HEIGHT - text_h - 2:
            dy = -dy
    return False


async def _hacker_text(duration=12):
    """Returns True if exited by button press."""
    lines_pool = [
        "SCANNING NETWORK",
        "CRACKING HASHES",
        "BYPASSING FIREWALL",
        "INJECTING PAYLOAD",
        "ENUMERATING HOSTS",
        "EXFILTRATING DATA",
        "PIVOTING...",
        "ROOT ACQUIRED",
        "> B33 ONLINE",
        "STEALTH MODE: ON",
    ]
    shown = []
    loop = asyncio.get_running_loop()
    end = loop.time() + duration

    while loop.time() < end:
        if await _any_button(0.05):
            return True
        if len(shown) < 5:
            shown.append(random.choice(lines_pool))
        else:
            shown = shown[1:] + [random.choice(lines_pool)]
        display.show_glitch_frame(shown, 0.03)
        await asyncio.sleep(0.4)
    return False


async def _do_screensaver():
    """Screensaver: cycle through animations. Any button press exits."""
    while True:
        if await _matrix_rain(20):
            return
        if await _bounce_logo(15):
            return
        if await _hacker_text(12):
            return


# ── Menu actions ──────────────────────────────────────────────────────────────

async def _do_scan(cfg, api):
    global _last_scan_count
    display.show_status("Scanning LAN...", "Finding hosts")
    found = await scanner.run_lan_scan(wifi_manager, api, display=display)
    _last_scan_count = found
    print(f"[scan] Scan complete — found {found} hosts")
    display.flash()
    await asyncio.sleep(0.08)
    display.show_status("Scan complete!", f"Found: {found} hosts")
    await buttons.wait_enter()


async def _do_deploy_hid(cfg):
    os_options = ["Windows", "Linux", "Back"]
    os_sel = 0
    display.show_menu("Deploy HID", os_options, os_sel)

    while True:
        event = await buttons.read_event()
        if event == "down":
            os_sel = (os_sel + 1) % len(os_options)
            display.show_menu("Deploy HID", os_options, os_sel)
        elif event == "enter":
            choice = os_options[os_sel]
            if choice == "Back":
                return
            os_type = choice.lower()
            display.show_status("Deploying HID", f"Target: {choice}")
            ok = hid_controller.deploy(os_type, cfg["server_url"], cfg["api_key"])
            if ok:
                display.flash()
                await asyncio.sleep(0.08)
                display.show_status("Deploy OK!", f"{choice} done")
            else:
                display.show_status("Deploy FAILED", "Check Pico USB")
            await asyncio.sleep(2)
            return


async def _do_task_status(api):
    spin_task = asyncio.create_task(_spin("Checking tasks..."))
    try:
        loop = asyncio.get_running_loop()
        tasks = await loop.run_in_executor(None, api.poll)
    except Exception:
        tasks = []
    spin_task.cancel()
    pending = len(poller._pending_results)
    display.show_text([
        "Task Status",
        f"Local queue: {pending}",
        f"Server tasks: {len(tasks)}",
        f"Last scan: {_last_scan_count if _last_scan_count is not None else 'N/A'} hosts",
        "ENTER to go back",
    ])
    await buttons.wait_enter()


async def _do_settings(cfg):
    items = ["WiFi Info", "Server Info", "Back"]
    sel = 0
    display.show_menu("Settings", items, sel)

    while True:
        event = await buttons.read_event()
        if event == "down":
            sel = (sel + 1) % len(items)
            display.show_menu("Settings", items, sel)
        elif event == "enter":
            choice = items[sel]
            if choice == "Back":
                return
            elif choice == "WiFi Info":
                display.show_text([
                    "WiFi Info",
                    f"SSID: {_ssid[:18] if _ssid else 'None'}",
                    f"IP:   {_local_ip or 'N/A'}",
                    "",
                    "ENTER to go back",
                ])
                await buttons.wait_enter()
                display.show_menu("Settings", items, sel)
            elif choice == "Server Info":
                url_short = cfg["server_url"].replace("https://", "")[:21]
                status = "Online" if _server_ok else "Offline"
                display.show_text([
                    "Server Info",
                    url_short,
                    f"Status: {status}",
                    f"Poll:   {cfg['poll_interval']}s",
                    "ENTER to go back",
                ])
                await buttons.wait_enter()
                display.show_menu("Settings", items, sel)


# ── Main menu loop ────────────────────────────────────────────────────────────

async def _menu_loop(cfg, api):
    global _selected
    display.show_menu("B33 Main Menu", _MENU_ITEMS, _selected, _status_line())

    while True:
        # Auto-screensaver after inactivity
        try:
            event = await asyncio.wait_for(buttons.read_event(), timeout=_SCREENSAVER_TIMEOUT)
        except asyncio.TimeoutError:
            await _do_screensaver()
            display.show_menu("B33 Main Menu", _MENU_ITEMS, _selected, _status_line())
            continue

        if event == "down":
            _selected = (_selected + 1) % len(_MENU_ITEMS)
            display.show_menu("B33 Main Menu", _MENU_ITEMS, _selected, _status_line())

        elif event == "enter":
            choice = _MENU_ITEMS[_selected]

            if choice == "Scan LAN":
                await _do_scan(cfg, api)
            elif choice == "Deploy HID":
                await _do_deploy_hid(cfg)
            elif choice == "Task Status":
                await _do_task_status(api)
            elif choice == "Settings":
                await _do_settings(cfg)
            elif choice == "Screensaver":
                await _do_screensaver()

            display.show_menu("B33 Main Menu", _MENU_ITEMS, _selected, _status_line())


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    global _server_ok, _ssid, _local_ip

    # 1. Display init
    try:
        display.init()
    except Exception as e:
        print(f"[main] Display init failed: {e}. Continuing without display.")

    # 2. Boot animation
    await _boot_animation()

    # 3. Buttons
    try:
        buttons.init()
    except Exception as e:
        print(f"[main] Buttons init failed: {e}")

    # 4. Config
    try:
        cfg = config.load()
    except RuntimeError as e:
        display.show_status("Config Error", str(e)[:21])
        print(f"[main] {e}")
        sys.exit(1)

    # 5. WiFi
    _ssid = wifi_manager.get_ssid()
    _local_ip = wifi_manager.get_local_ip()
    if _ssid:
        display.show_status("WiFi OK", f"{_ssid}  {_local_ip}")
    else:
        display.show_status("WiFi?", "Not connected")
    await asyncio.sleep(1)

    # 6. Server health check with spinner
    api = api_module.ApiClient(cfg["server_url"], cfg["api_key"])
    spin_task = asyncio.create_task(_spin("Server check...", cfg["server_url"].split("//")[-1][:21]))
    loop = asyncio.get_running_loop()
    _server_ok = await loop.run_in_executor(None, api.health_check)
    spin_task.cancel()
    if _server_ok:
        display.flash()
        await asyncio.sleep(0.08)
        display.show_status("Server OK", "Connected")
    else:
        display.show_status("Server offline", "continuing...")
    await asyncio.sleep(1)

    # 7. Background poller
    asyncio.create_task(poller.run(api, task_runner, display, cfg["poll_interval"], cfg))

    # 8. Menu loop
    await _menu_loop(cfg, api)


if __name__ == "__main__":
    asyncio.run(main())
