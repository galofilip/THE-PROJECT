import asyncio
import json
import subprocess
import time
import xml.etree.ElementTree as ET

import requests

_PORTS = "21,22,23,25,53,80,135,139,443,445,3306,3389,5900,8080,8443"
_NSE_SCRIPTS = (
    "banner,ftp-anon,ssh-auth-methods,ssl-enum-ciphers,"
    "smb-security-mode,smb2-security-mode,http-headers,"
    "mysql-empty-password,vnc-info,rdp-enum-encryption"
)
_NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_NVD_TIMEOUT = 8
_NVD_DELAY = 6  # stay under NVD's 5 req/30s unauthenticated limit
_MAX_CVE_QUERIES = 5  # per host


def _run_nmap(args, timeout=120):
    try:
        result = subprocess.run(
            ["sudo", "nmap"] + args + ["-oX", "-"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.stderr:
            print(f"[scanner] nmap stderr: {result.stderr[:300]}")
        if not result.stdout.strip():
            print(f"[scanner] nmap returned empty stdout (exit code {result.returncode})")
        return result.stdout
    except subprocess.TimeoutExpired:
        print("[scanner] nmap timed out")
        return ""
    except FileNotFoundError:
        print("[scanner] nmap not found — install with: sudo apt install nmap")
        return ""
    except Exception as e:
        print(f"[scanner] nmap error: {e}")
        return ""


def _parse_host(host_el):
    data = {"target_ip": "", "mac_address": "", "hostname": "", "os": {}, "ports": []}

    for addr in host_el.findall("address"):
        if addr.get("addrtype") == "ipv4":
            data["target_ip"] = addr.get("addr", "")
        elif addr.get("addrtype") == "mac":
            data["mac_address"] = addr.get("addr", "")

    for hn in host_el.findall("hostnames/hostname"):
        data["hostname"] = hn.get("name", "")
        break

    osmatch = host_el.find("os/osmatch")
    if osmatch is not None:
        osclass = osmatch.find("osclass")
        data["os"] = {
            "name": osmatch.get("name", ""),
            "accuracy": int(osmatch.get("accuracy", 0)),
            "family": osclass.get("osfamily", "") if osclass is not None else "",
        }

    for port_el in host_el.findall("ports/port"):
        state = port_el.find("state")
        if state is None or state.get("state") != "open":
            continue

        port_num = int(port_el.get("portid", 0))
        svc = port_el.find("service")

        port_data = {
            "port": port_num,
            "service": svc.get("name", "").upper() if svc is not None else "",
            "product": svc.get("product", "") if svc is not None else "",
            "version": svc.get("version", "") if svc is not None else "",
            "cpe": "",
            "scripts": {},
        }

        if svc is not None:
            cpe_el = svc.find("cpe")
            if cpe_el is not None:
                port_data["cpe"] = cpe_el.text or ""

        for script in port_el.findall("script"):
            sid = script.get("id", "")
            output = script.get("output", "").strip()
            if sid and output:
                port_data["scripts"][sid] = output

        data["ports"].append(port_data)

    return data


def _cpe22_to_23(cpe22):
    """Convert nmap CPE 2.2 string to CPE 2.3 for NVD API."""
    if not cpe22.startswith("cpe:/"):
        return None
    parts = cpe22[5:].split(":")
    while len(parts) < 4:
        parts.append("*")
    return "cpe:2.3:" + ":".join(parts[:4]) + ":*:*:*:*:*:*:*"


def _parse_version(ver_str):
    """Parse version string into a comparable tuple. Strips suffixes like p2, b1, -rc1."""
    if not ver_str:
        return None
    try:
        clean = ver_str.strip().split("-")[0].split("p")[0].split("b")[0]
        parts = [int(x) for x in clean.split(".") if x.isdigit()]
        return tuple(parts) if parts else None
    except Exception:
        return None


def _version_in_range(detected_ver, start_incl, start_excl, end_incl, end_excl):
    """Return True if detected_ver falls within a CVE's affected version range."""
    v = _parse_version(detected_ver)
    if v is None:
        return True  # can't parse — don't filter out
    if start_incl:
        s = _parse_version(start_incl)
        if s and v < s:
            return False
    if start_excl:
        s = _parse_version(start_excl)
        if s and v <= s:
            return False
    if end_incl:
        e = _parse_version(end_incl)
        if e and v > e:
            return False
    if end_excl:
        e = _parse_version(end_excl)
        if e and v >= e:
            return False
    return True


def _cve_affects_version(cve, detected_ver):
    """Check whether the CVE's version ranges include detected_ver.
    Returns True if no version data is present (can't disprove applicability)."""
    if not detected_ver:
        return True

    nodes = []
    for config in cve.get("configurations", []):
        nodes.extend(config.get("nodes", []))

    if not nodes:
        return True

    for node in nodes:
        for match in node.get("cpeMatch", []):
            if not match.get("vulnerable", False):
                continue
            if _version_in_range(
                detected_ver,
                match.get("versionStartIncluding"),
                match.get("versionStartExcluding"),
                match.get("versionEndIncluding"),
                match.get("versionEndExcluding"),
            ):
                return True

    return False


def _lookup_cves(cpe=None, keyword=None, detected_ver=None, nvd_api_key=None):
    try:
        headers = {}
        if nvd_api_key:
            headers["apiKey"] = nvd_api_key

        if cpe:
            cpe23 = _cpe22_to_23(cpe)
            if not cpe23:
                return []
            params = {"cpeName": cpe23, "resultsPerPage": 20}
        else:
            params = {"keywordSearch": keyword, "resultsPerPage": 10}

        r = requests.get(_NVD_URL, params=params, headers=headers, timeout=_NVD_TIMEOUT)
        cves = []
        for item in r.json().get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id", "")
            if not cve_id:
                continue

            desc = ""
            for d in cve.get("descriptions", []):
                if d.get("lang") == "en":
                    desc = d.get("value", "")
                    break

            severity = ""
            metrics = cve.get("metrics", {})
            for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                entries = metrics.get(key, [])
                if entries:
                    severity = entries[0].get("cvssData", {}).get("baseSeverity", "")
                    break

            # Only keep HIGH and CRITICAL — NVD's cvssV3Severity param doesn't accept
            # comma-separated values so we filter here instead
            if severity not in ("HIGH", "CRITICAL"):
                print(f"[scanner] Skipping {cve_id} — severity {severity or 'none'} not HIGH/CRITICAL")
                continue

            if not _cve_affects_version(cve, detected_ver):
                print(f"[scanner] Skipping {cve_id} — version range doesn't match {detected_ver}")
                continue

            cves.append({"id": cve_id, "severity": severity, "description": desc})
        return cves
    except Exception as e:
        print(f"[scanner] CVE lookup failed: {e}")
        return []


def _calc_risk(ports, vulnerabilities):
    severities = {v.get("severity", "") for v in vulnerabilities}
    if "CRITICAL" in severities:
        return "critical"

    script_findings = {}
    for p in ports:
        script_findings.update(p.get("scripts", {}))

    ftp_anon = script_findings.get("ftp-anon", "")
    if ftp_anon and "allowed" in ftp_anon.lower():
        return "high"
    if "mysql-empty-password" in script_findings:
        return "high"
    smb_mode = script_findings.get("smb-security-mode", "")
    if "disabled" in smb_mode:
        return "high"

    service_names = {p["service"] for p in ports}
    if "HIGH" in severities or service_names & {"TELNET", "RDP", "VNC"}:
        return "high"
    if "MEDIUM" in severities or service_names & {"NETBIOS", "SMB", "MYSQL"}:
        return "medium"
    if ports:
        return "low"
    return "none"


def scan_host(ip, timeout=120, nvd_api_key=None):
    """Full nmap scan of a single host. Returns dict ready for POST /api/scans/private.
    Also includes '_os' key (stripped before DB push) for use in Groq prompt."""
    print(f"[scanner] Scanning {ip}")

    xml_out = _run_nmap([
        "-sS", "-sV", "-O", "-T4", "--open",
        "-p", _PORTS,
        "--script", _NSE_SCRIPTS,
        ip,
    ], timeout=timeout)

    if not xml_out:
        print(f"[scanner] Retrying {ip} without sudo features")
        xml_out = _run_nmap(["-sT", "-sV", "-T4", "--open", "-p", _PORTS, ip], timeout=timeout)

    if not xml_out:
        return None

    try:
        root = ET.fromstring(xml_out)
    except ET.ParseError as e:
        print(f"[scanner] XML parse error for {ip}: {e}")
        return None

    host_el = root.find("host")
    if host_el is None:
        return None

    host = _parse_host(host_el)
    if not host["target_ip"]:
        host["target_ip"] = ip

    # CVE lookup — deduplicated, max _MAX_CVE_QUERIES per host
    vulnerabilities = []
    queried = set()
    query_count = 0

    for port in host["ports"]:
        if query_count >= _MAX_CVE_QUERIES:
            break

        cpe = port.get("cpe", "")
        product = port.get("product", "")
        version = port.get("version", "")
        key = cpe or f"{product} {version}".strip()

        if not key or key in queried:
            continue
        queried.add(key)

        if cpe:
            cves = _lookup_cves(cpe=cpe, detected_ver=version, nvd_api_key=nvd_api_key)
        elif product:
            keyword = f"{product} {version}".strip() if version else product
            cves = _lookup_cves(keyword=keyword, detected_ver=version, nvd_api_key=nvd_api_key)
        else:
            continue

        vulnerabilities.extend(cves)
        query_count += 1
        if query_count < _MAX_CVE_QUERIES:
            time.sleep(_NVD_DELAY)

    return {
        "target_ip": host["target_ip"],
        "mac_address": host["mac_address"],
        "hostname": host["hostname"],
        "open_ports": json.dumps([p["port"] for p in host["ports"]]),
        "detected_services": json.dumps(host["ports"]),
        "vulnerabilities_found": json.dumps(vulnerabilities),
        "risk_level": _calc_risk(host["ports"], vulnerabilities),
        "scan_source": "pi4",
        "_os": host["os"],  # stripped before DB push — used only for Groq prompt
    }


def _discover_hosts(subnet):
    """ARP/ICMP ping sweep. Returns list of live IPs."""
    print(f"[scanner] Discovering hosts on {subnet}/24")
    xml_out = _run_nmap(["-sn", "-T4", f"{subnet}.0/24"], timeout=60)
    if not xml_out:
        return []

    try:
        root = ET.fromstring(xml_out)
    except ET.ParseError:
        return []

    hosts = []
    for host_el in root.findall("host"):
        state = host_el.find("status")
        if state is None or state.get("state") != "up":
            continue
        for addr in host_el.findall("address"):
            if addr.get("addrtype") == "ipv4":
                ip = addr.get("addr", "")
                if ip:
                    hosts.append(ip)
                break

    return hosts


async def run_lan_scan(wifi_manager, api_client, display=None, cfg=None):
    subnet = wifi_manager.get_subnet_base()
    ssid = wifi_manager.get_ssid()
    bssid = wifi_manager.get_bssid()
    nvd_api_key = (cfg or {}).get("nvd_api_key", "")

    if not subnet:
        print("[scanner] Could not determine subnet.")
        return 0

    hosts = _discover_hosts(subnet)
    print(f"[scanner] Found {len(hosts)} live hosts")

    found = 0
    for i, ip in enumerate(hosts):
        if display:
            display.show_progress(f"Scanning {ip}", i + 1, len(hosts))

        result = scan_host(ip, nvd_api_key=nvd_api_key)
        if result:
            result["network_ssid"] = ssid
            result["network_bssid"] = bssid
            result.pop("_os", None)  # not a DB field
            ok = api_client.push_scan(result)
            print(f"[scanner] push_scan {ip}: {'ok' if ok else 'FAILED'}")
            found += 1

        await asyncio.sleep(0)

    return found
