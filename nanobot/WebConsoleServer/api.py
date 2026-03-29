"""API endpoints for the WebConsoleServer dashboard."""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from nanobot.WebConsoleServer.summary import build_system_summary
from nanobot.supervisor.models import Task

router = APIRouter(tags=["webconsole-api"])

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SBIN_DIR = _REPO_ROOT / "sbin"
_CONTROL_ACTIONS: dict[tuple[str, str], list[str]] = {
    ("gateway", "start"): ["start-nanobot.sh"],
    ("gateway", "stop"): ["stop-nanobot.sh"],
    ("gateway", "restart"): ["stop-nanobot.sh", "start-nanobot.sh"],
    ("supervisor", "start"): ["start-supervisor.sh"],
    ("supervisor", "stop"): ["stop-supervisor.sh"],
    ("supervisor", "restart"): ["stop-supervisor.sh", "start-supervisor.sh"],
    ("cluster", "restart"): ["restart-nanobot.sh"],
    ("runtime", "status"): ["nanobot-status.sh"],
}
_DISRUPTIVE_ACTIONS = {
    ("supervisor", "stop"),
    ("supervisor", "restart"),
    ("cluster", "restart"),
}


class QuickTaskBody(BaseModel):
    instruction: str = Field(min_length=1, max_length=4000)
    label: str = Field(default="", max_length=200)


def _resolve_script(script_name: str) -> Path:
    script_path = _SBIN_DIR / script_name
    if not script_path.exists():
        raise HTTPException(status_code=500, detail=f"Missing control script: {script_name}")
    return script_path


async def _run_script(script_name: str) -> dict[str, Any]:
    script_path = _resolve_script(script_name)
    process = await asyncio.create_subprocess_exec(
        "bash",
        str(script_path),
        cwd=str(_REPO_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "script": script_name,
        "returncode": process.returncode,
        "stdout": stdout.decode("utf-8", errors="replace").strip(),
        "stderr": stderr.decode("utf-8", errors="replace").strip(),
    }


async def _schedule_disruptive_action(scripts: list[str]) -> None:
    (Path(_REPO_ROOT) / "logs").mkdir(parents=True, exist_ok=True)
    log_file = _REPO_ROOT / "logs" / "webconsole-control.log"
    commands = " && ".join(
        f"bash {shlex.quote(str(_resolve_script(script_name)))}" for script_name in scripts
    )
    delayed_command = (
        f"sleep 1; cd {shlex.quote(str(_REPO_ROOT))}; "
        f"{commands} >> {shlex.quote(str(log_file))} 2>&1"
    )
    launcher = f"nohup bash -lc {shlex.quote(delayed_command)} >/dev/null 2>&1 &"
    process = await asyncio.create_subprocess_exec(
        "bash",
        "-lc",
        launcher,
        cwd=str(_REPO_ROOT),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()


def _summarize_results(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for result in results:
        output = result["stdout"] or result["stderr"] or "completed"
        parts.append(f"{result['script']}: {output.splitlines()[0]}")
    return " | ".join(parts)


@router.get("/webconsole/summary")
async def webconsole_summary(request: Request) -> dict:
    return await build_system_summary(request.app)


@router.post("/webconsole/tasks/quick-create")
async def webconsole_quick_create_task(body: QuickTaskBody, request: Request) -> dict[str, Any]:
    registry = request.app.state.worker_registry
    task = await registry.create_task(
        Task(
            instruction=body.instruction,
            label=body.label,
            origin_channel="webconsole",
            origin_chat_id="console",
            session_key="webconsole",
            max_iterations=registry.task_default_max_iterations,
            timeout_s=registry.task_default_timeout_s,
        )
    )
    return {
        "ok": True,
        "message": f"Task {task.task_id} created.",
        "task": {
            "task_id": task.task_id,
            "label": task.label,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        },
    }


@router.post("/webconsole/control/{target}/{action}")
async def webconsole_control(target: str, action: str, request: Request) -> dict[str, Any]:
    del request
    scripts = _CONTROL_ACTIONS.get((target, action))
    if scripts is None:
        raise HTTPException(status_code=404, detail=f"Unsupported control action: {target}/{action}")

    if (target, action) in _DISRUPTIVE_ACTIONS:
        await _schedule_disruptive_action(scripts)
        return {
            "ok": True,
            "scheduled": True,
            "target": target,
            "action": action,
            "message": "Action scheduled. The console may disconnect briefly while the supervisor restarts.",
        }

    results = [await _run_script(script_name) for script_name in scripts]
    failures = [result for result in results if result["returncode"] != 0]
    if failures:
        failure_output = failures[0]["stderr"] or failures[0]["stdout"] or "control command failed"
        raise HTTPException(status_code=500, detail=failure_output)

    return {
        "ok": True,
        "scheduled": False,
        "target": target,
        "action": action,
        "message": _summarize_results(results),
        "results": results,
    }