import subprocess


def _run(cmd):
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def is_connected():
    out = _run(["nmcli", "-t", "-f", "STATE", "general"])
    return "connected" in out


def get_ssid():
    out = _run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
    for line in out.splitlines():
        if line.startswith("yes:"):
            return line.split(":", 1)[1]
    return ""


def get_bssid():
    out = _run(["nmcli", "-t", "-f", "active,bssid", "dev", "wifi"])
    for line in out.splitlines():
        if line.startswith("yes:"):
            return line.split(":", 1)[1]
    return ""


def get_local_ip():
    out = _run(["hostname", "-I"])
    parts = out.split()
    return parts[0] if parts else ""


def get_gateway_ip():
    out = _run(["ip", "route", "show", "default"])
    # "default via 192.168.1.1 dev wlan0 ..."
    for part in out.split():
        if part not in ("default", "via") and _looks_like_ip(part):
            return part
    return ""


def get_subnet_base():
    """Return the first three octets of the gateway, e.g. '192.168.1'."""
    gw = get_gateway_ip()
    if gw:
        parts = gw.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3])
    return ""


def _looks_like_ip(s):
    parts = s.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
