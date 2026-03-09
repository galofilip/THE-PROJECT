import sys
import json
import supervisor

# Disable auto-reload so the serial port stays stable
supervisor.runtime.autoreload = False

import hid_payload


def _respond(status, message=""):
    sys.stdout.write(json.dumps({"status": status, "message": message}) + "\n")


def _read_line():
    buf = ""
    while True:
        ch = sys.stdin.read(1)
        if ch == "\n":
            return buf.strip()
        buf += ch


def main():
    _respond("ready", "B33 Pico HID v1.0 — waiting for commands")

    while True:
        try:
            line = _read_line()
            if not line:
                continue

            cmd = json.loads(line)
            os_type = cmd.get("os", "").lower()
            server_url = cmd.get("server_url", "")
            api_key = cmd.get("api_key", "")

            if not server_url or not api_key:
                _respond("error", "missing server_url or api_key")
                continue

            if os_type == "windows":
                hid_payload.deploy_windows(server_url, api_key)
                _respond("ok")
            elif os_type == "linux":
                hid_payload.deploy_linux(server_url, api_key)
                _respond("ok")
            else:
                _respond("error", f"unknown os: {os_type}")

        except ValueError as e:
            _respond("error", f"invalid JSON: {e}")
        except Exception as e:
            _respond("error", str(e))


main()
