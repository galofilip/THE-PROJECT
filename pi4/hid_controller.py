import glob
import json
import time
import serial

_BAUD = 115200
_TIMEOUT = 30  # seconds to wait for Pico response after sending command


def find_pico_port():
    """Return the first /dev/ttyACM* or /dev/ttyUSB* device found."""
    for pattern in ("/dev/ttyACM*", "/dev/ttyUSB*"):
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def deploy(os_type, server_url, api_key):
    """
    Send a deploy command to the Pico over USB serial.
    os_type: 'windows' or 'linux'
    Returns True on success, False on failure.
    """
    port = find_pico_port()
    if not port:
        print("[hid] No Pico found on serial ports.")
        return False

    command = json.dumps({
        "os": os_type,
        "server_url": server_url,
        "api_key": api_key,
    }) + "\n"

    try:
        with serial.Serial(port, _BAUD, timeout=_TIMEOUT) as ser:
            time.sleep(1)  # give Pico time to settle after connection
            ser.write(command.encode())
            ser.flush()
            # Wait for response
            raw = ser.readline()
            if raw:
                response = json.loads(raw.decode().strip())
                if response.get("status") == "ok":
                    print(f"[hid] Deploy to {os_type} succeeded.")
                    return True
                else:
                    print(f"[hid] Pico error: {response.get('message', 'unknown')}")
    except serial.SerialException as e:
        print(f"[hid] Serial error: {e}")
    except Exception as e:
        print(f"[hid] Unexpected error: {e}")

    return False
