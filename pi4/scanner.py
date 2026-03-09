import asyncio
import json
import socket
import requests

_PORTS = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 3306, 3389, 5900, 8080, 8443]

_SERVICE_MAP = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    135: "RPC",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    5900: "VNC",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
}

# Services worth querying NVD for (skip low-signal ones)
_SCAN_CVE_FOR = {"SSH", "FTP", "Telnet", "SMB", "MySQL", "RDP", "VNC", "HTTP", "HTTPS"}

_NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_NVD_TIMEOUT = 8


def _is_host_up(ip, timeout):
    """Try TCP connect to port 80, 443, then 22. Refused = up; timeout = down."""
    for port in (80, 443, 22):
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except ConnectionRefusedError:
            return True  # port closed but host responded
        except OSError:
            continue
    return False


def _scan_ports(ip, timeout):
    open_ports = []
    for port in _PORTS:
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                open_ports.append(port)
        except ConnectionRefusedError:
            pass
        except OSError:
            pass
    return open_ports


def _lookup_cves(service_name):
    try:
        r = requests.get(
            _NVD_URL,
            params={"keywordSearch": service_name, "resultsPerPage": 3},
            timeout=_NVD_TIMEOUT,
        )
        items = r.json().get("vulnerabilities", [])
        cves = []
        for item in items:
            cve = item.get("cve", {})
            cve_id = cve.get("id", "")
            desc = ""
            for d in cve.get("descriptions", []):
                if d.get("lang") == "en":
                    desc = d.get("value", "")[:100]
                    break
            severity = ""
            metrics = cve.get("metrics", {})
            v31 = metrics.get("cvssMetricV31", [])
            if v31:
                severity = v31[0].get("cvssData", {}).get("baseSeverity", "")
            if cve_id:
                cves.append({"id": cve_id, "severity": severity, "description": desc})
        return cves
    except Exception as e:
        print(f"[scanner] CVE lookup failed for {service_name}: {e}")
        return []


def _calc_risk(open_ports, services, vulnerabilities):
    severities = {v.get("severity", "") for v in vulnerabilities}
    if "CRITICAL" in severities:
        return "critical"
    service_names = set(services.values())
    if "HIGH" in severities or service_names & {"Telnet", "RDP", "VNC"}:
        return "high"
    if "MEDIUM" in severities or service_names & {"SMB", "MySQL"}:
        return "medium"
    if open_ports:
        return "low"
    return "none"


def scan_host(ip, timeout=0.5):
    """Scan a single host. Returns a dict ready to POST to /api/scans/private."""
    open_ports = _scan_ports(ip, timeout)
    services = {p: _SERVICE_MAP[p] for p in open_ports if p in _SERVICE_MAP}

    vulnerabilities = []
    queried = set()
    for svc in services.values():
        if svc in _SCAN_CVE_FOR and svc not in queried:
            queried.add(svc)
            vulnerabilities.extend(_lookup_cves(svc))

    risk = _calc_risk(open_ports, services, vulnerabilities)
    service_list = [{"port": p, "service": s} for p, s in services.items()]

    return {
        "target_ip": ip,
        "open_ports": json.dumps(open_ports),
        "detected_services": json.dumps(service_list),
        "vulnerabilities_found": json.dumps(vulnerabilities),
        "risk_level": risk,
        "scan_source": "pico",
    }


async def run_lan_scan(wifi_manager, api_client, display=None):
    """Discover and scan all hosts on the current subnet, pushing each result immediately."""
    subnet = wifi_manager.get_subnet_base()
    ssid = wifi_manager.get_ssid()
    bssid = wifi_manager.get_bssid()
    timeout = 0.5

    if not subnet:
        print("[scanner] Could not determine subnet.")
        return 0

    found = 0
    total = 254
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        if display:
            display.show_progress(f"Scanning {subnet}.x", i, total)

        if _is_host_up(ip, timeout):
            result = scan_host(ip, timeout)
            result["network_ssid"] = ssid
            result["network_bssid"] = bssid
            api_client.push_scan(result)
            found += 1

        await asyncio.sleep(0)  # yield to event loop

    return found
