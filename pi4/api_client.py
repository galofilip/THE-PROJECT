import time
import requests

_HEALTH_RETRIES = 3
_HEALTH_RETRY_DELAY = 15  # seconds between retries (Render cold start)
_TIMEOUT = 10


class ApiClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip("/")
        self._headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def health_check(self):
        """GET /api/health — retries 3x to handle Render cold start (~30-50s)."""
        for attempt in range(_HEALTH_RETRIES):
            try:
                r = requests.get(
                    f"{self.server_url}/api/health",
                    timeout=_TIMEOUT,
                )
                if r.status_code == 200:
                    return True
            except requests.RequestException as e:
                print(f"[api] health_check attempt {attempt + 1} failed: {e}")
            if attempt < _HEALTH_RETRIES - 1:
                time.sleep(_HEALTH_RETRY_DELAY)
        return False

    def poll(self, completed_tasks=None):
        """POST /api/pico/poll — send completed tasks, receive new ones."""
        body = {}
        if completed_tasks:
            body["completed_tasks"] = completed_tasks
        try:
            r = requests.post(
                f"{self.server_url}/api/pico/poll",
                json=body,
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            data = r.json()
            if data.get("success"):
                return data.get("data", {}).get("tasks", [])
        except Exception as e:
            print(f"[api] poll error: {e}")
        return []

    def update_task(self, task_id, status, result=None, error_message=None):
        """PATCH /api/tasks/{id} — update task status and result."""
        body = {"status": status}
        if result is not None:
            body["result"] = result
        if error_message is not None:
            body["error_message"] = error_message
        try:
            r = requests.patch(
                f"{self.server_url}/api/tasks/{task_id}",
                json=body,
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            if not r.json().get("success", False):
                print(f"[api] update_task FAILED ({r.status_code}): {r.text[:200]}")
                return False
            return True
        except Exception as e:
            print(f"[api] update_task error: {e}")
            return False

    def get_approved_exploits(self):
        """GET /api/tasks?status=approved — fetch approved exploit tasks."""
        try:
            r = requests.get(
                f"{self.server_url}/api/tasks?status=approved",
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            data = r.json()
            if data.get("success"):
                tasks = data.get("data", [])
                return [t for t in tasks if t.get("task_type") == "exploit"]
        except Exception as e:
            print(f"[api] get_approved_exploits error: {e}")
        return []

    def push_scan(self, scan_dict):
        """POST /api/scans/private — push a single host's scan result."""
        try:
            r = requests.post(
                f"{self.server_url}/api/scans/private",
                json=scan_dict,
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            return r.json().get("success", False)
        except Exception as e:
            print(f"[api] push_scan error: {e}")
            return False
