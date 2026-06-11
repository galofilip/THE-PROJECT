import json
import os

_SETTINGS_PATH = (
    "/boot/firmware/b33_settings.json"
    if os.path.exists("/boot/firmware/b33_settings.json")
    else "/boot/b33_settings.json"
)

_defaults = {
    "server_url": "https://the-project-gukh.onrender.com",
    "api_key": "",
    "poll_interval": 30,
    "scan_timeout": 0.5,
    "groq_api_key": "",
    "nvd_api_key": "",
}


def load():
    settings = dict(_defaults)

    if os.path.exists(_SETTINGS_PATH):
        try:
            with open(_SETTINGS_PATH) as f:
                settings.update(json.load(f))
        except Exception as e:
            print(f"[config] Warning: could not read {_SETTINGS_PATH}: {e}")

    # Environment variable overrides (useful for dev on a laptop)
    for key in ("server_url", "api_key"):
        env_val = os.environ.get(f"B33_{key.upper()}")
        if env_val:
            settings[key] = env_val

    if not settings["api_key"]:
        raise RuntimeError(
            f"B33_API_KEY not set. Add it to {_SETTINGS_PATH} or set the B33_API_KEY env var."
        )

    return settings
