import asyncio

_pending_results = []


def add_result(task_id, status, result="", error_message=""):
    """Called by task_runner when a task completes."""
    _pending_results.append({
        "task_id": task_id,
        "status": status,
        "result": result,
        "error_message": error_message,
    })


async def run(api_client, task_runner, display, poll_interval, cfg):
    """Background asyncio task: poll server every poll_interval seconds."""
    while True:
        await asyncio.sleep(poll_interval)
        try:
            # 1. Send completed task results + fetch new pending tasks
            completed = list(_pending_results)
            _pending_results.clear()

            tasks = api_client.poll(completed_tasks=completed if completed else None)
            for task in tasks:
                asyncio.create_task(task_runner.dispatch(task, api_client, cfg))

            # 2. Fetch approved exploit tasks (user reviewed and approved in web UI)
            approved = api_client.get_approved_exploits()
            for task in approved:
                asyncio.create_task(task_runner.dispatch_approved(task, api_client))

        except Exception as e:
            print(f"[poller] Error: {e}")
