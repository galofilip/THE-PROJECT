import asyncio
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

_MENU_ITEMS = ["Scan LAN", "Deploy HID", "Task Status", "Settings"]
_selected = 0


async def _menu_loop(cfg, api, display_mod):
    global _selected
    display_mod.show_menu("B33 Main Menu", _MENU_ITEMS, _selected)

    while True:
        event = await buttons.read_event()

        if event == "down":
            _selected = (_selected + 1) % len(_MENU_ITEMS)
            display_mod.show_menu("B33 Main Menu", _MENU_ITEMS, _selected)

        elif event == "enter":
            choice = _MENU_ITEMS[_selected]

            if choice == "Scan LAN":
                await _do_scan(cfg, api, display_mod)

            elif choice == "Deploy HID":
                await _do_deploy_hid(cfg, display_mod)

            elif choice == "Task Status":
                pending = len(poller._pending_results)
                display_mod.show_status("Task Status", f"Pending: {pending}")
                await asyncio.sleep(2)

            elif choice == "Settings":
                display_mod.show_status("Settings", f"Poll: {cfg['poll_interval']}s")
                await asyncio.sleep(2)

            display_mod.show_menu("B33 Main Menu", _MENU_ITEMS, _selected)


async def _do_scan(cfg, api, display_mod):
    display_mod.show_status("Scanning LAN...", "Finding hosts")
    found = await scanner.run_lan_scan(wifi_manager, api, display=display_mod)
    print(f"[scan] Scan complete — found {found} hosts")
    display_mod.show_status("Scan complete", f"Found: {found} hosts")
    await buttons.wait_enter()


async def _do_deploy_hid(cfg, display_mod):
    os_options = ["Windows", "Linux", "Cancel"]
    os_selected = 0
    display_mod.show_menu("Deploy HID", os_options, os_selected)

    while True:
        event = await buttons.read_event()
        if event == "down":
            os_selected = (os_selected + 1) % len(os_options)
            display_mod.show_menu("Deploy HID", os_options, os_selected)
        elif event == "enter":
            choice = os_options[os_selected]
            if choice == "Cancel":
                return
            os_type = choice.lower()
            display_mod.show_status("Deploying HID", f"Target: {choice}")
            ok = hid_controller.deploy(os_type, cfg["server_url"], cfg["api_key"])
            if ok:
                display_mod.show_status("Deploy OK", f"{choice} done")
            else:
                display_mod.show_status("Deploy FAILED", "Check Pico USB")
            await asyncio.sleep(2)
            return


async def main():
    # 1. Display
    try:
        display.init()
    except Exception as e:
        print(f"[main] Display init failed: {e}. Continuing without display.")

    display.show_text(["B33 v1.0", "Initializing..."])

    # 2. Buttons
    try:
        buttons.init()
    except Exception as e:
        print(f"[main] Buttons init failed: {e}")

    # 3. Config
    try:
        cfg = config.load()
    except RuntimeError as e:
        display.show_status("Config Error", str(e)[:21])
        print(f"[main] {e}")
        sys.exit(1)

    # 4. WiFi status
    ssid = wifi_manager.get_ssid()
    ip = wifi_manager.get_local_ip()
    if ssid:
        display.show_status("WiFi OK", f"{ssid} {ip}")
    else:
        display.show_status("WiFi?", "Not connected")
    await asyncio.sleep(1)

    # 5. Server health check
    api = api_module.ApiClient(cfg["server_url"], cfg["api_key"])
    display.show_status("Server check...", cfg["server_url"].split("//")[-1][:21])
    online = api.health_check()
    if online:
        display.show_status("Server OK", "")
    else:
        display.show_status("Server offline", "continuing...")
    await asyncio.sleep(1)

    # 6. Start background poller
    asyncio.create_task(
        poller.run(api, task_runner, display, cfg["poll_interval"])
    )

    # 7. Menu loop
    await _menu_loop(cfg, api, display)


if __name__ == "__main__":
    asyncio.run(main())
