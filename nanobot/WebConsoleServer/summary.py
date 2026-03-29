"""Summary builder for the phase-1 WebConsoleServer dashboard."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from nanobot.supervisor.models import PlanStatus, TaskStatus, WorkerStatus


def _status_counts(values: list[str], expected: list[str]) -> dict[str, int]:
    counts = {name: 0 for name in expected}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _derive_system_status(worker_counts: dict[str, int], task_counts: dict[str, int]) -> dict[str, str]:
    total_workers = worker_counts.get("total", 0)
    active_tasks = task_counts.get(TaskStatus.RUNNING.value, 0) + task_counts.get(TaskStatus.ASSIGNED.value, 0)
    unhealthy_workers = worker_counts.get(WorkerStatus.UNHEALTHY.value, 0) + worker_counts.get(WorkerStatus.OFFLINE.value, 0)

    if total_workers == 0:
        return {
            "tone": "pending",
            "label": "Waiting For Workers",
            "detail": "Phase-1 入口页已就绪，当前还没有任何 worker 注册到 supervisor。",
        }
    if unhealthy_workers > 0:
        return {
            "tone": "degraded",
            "label": "Degraded",
            "detail": f"检测到 {unhealthy_workers} 个 worker 处于离线或异常状态，需要人工关注。",
        }
    if active_tasks > 0:
        return {
            "tone": "healthy",
            "label": "Active",
            "detail": f"当前有 {active_tasks} 个任务正在执行或等待 worker 消化。",
        }
    return {
        "tone": "healthy",
        "label": "Idle And Ready",
        "detail": "所有在线 worker 均空闲，系统可以接收新的任务与计划。",
    }


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _component_snapshot(name: str, label: str, pidfile: Path) -> dict[str, Any]:
    if not pidfile.exists():
        return {
            "name": name,
            "label": label,
            "state": "stopped",
            "pid": None,
            "detail": "No pid file found.",
        }

    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (TypeError, ValueError):
        return {
            "name": name,
            "label": label,
            "state": "stale",
            "pid": None,
            "detail": f"Invalid pid file: {pidfile.name}",
        }

    if _is_pid_running(pid):
        return {
            "name": name,
            "label": label,
            "state": "running",
            "pid": pid,
            "detail": f"PID {pid} is alive.",
        }

    return {
        "name": name,
        "label": label,
        "state": "stale",
        "pid": pid,
        "detail": f"Stale pid file: {pidfile.name}",
    }


def _build_runtime_summary() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    pid_dir = Path(os.environ.get("NANOBOT_PID_DIR", str(repo_root / "pids")))
    log_dir = Path(os.environ.get("NANOBOT_LOG_DIR", str(repo_root / "logs")))

    components = [
        _component_snapshot("gateway", "Gateway", pid_dir / "nanobot-gateway.pid"),
        _component_snapshot("supervisor", "Supervisor", pid_dir / "nanobot-supervisor.pid"),
    ]

    worker_pidfiles = sorted(pid_dir.glob("nanobot-worker-*.pid")) if pid_dir.exists() else []
    for pidfile in worker_pidfiles:
        suffix = pidfile.stem.removeprefix("nanobot-")
        components.append(_component_snapshot(suffix, f"Worker {suffix.split('-')[-1]}", pidfile))

    running = sum(1 for item in components if item["state"] == "running")
    stale = sum(1 for item in components if item["state"] == "stale")
    stopped = sum(1 for item in components if item["state"] == "stopped")

    return {
        "components": components,
        "counts": {
            "running": running,
            "stale": stale,
            "stopped": stopped,
            "total": len(components),
        },
        "pid_dir": str(pid_dir),
        "log_dir": str(log_dir),
    }


async def build_system_summary(app: FastAPI) -> dict[str, Any]:
    registry = app.state.worker_registry
    now = time.time()

    workers = await registry.list_workers()
    tasks = await registry.list_tasks()
    plans = await registry.list_plans()

    worker_statuses = [worker.status.value if hasattr(worker.status, "value") else str(worker.status) for worker in workers]
    task_statuses = [task.status.value if hasattr(task.status, "value") else str(task.status) for task in tasks]
    plan_statuses = [plan.status.value if hasattr(plan.status, "value") else str(plan.status) for plan in plans]

    worker_counts = _status_counts(
        worker_statuses,
        [
            WorkerStatus.ONLINE.value,
            WorkerStatus.BUSY.value,
            WorkerStatus.UNHEALTHY.value,
            WorkerStatus.OFFLINE.value,
        ],
    )
    task_counts = _status_counts(
        task_statuses,
        [
            TaskStatus.PENDING.value,
            TaskStatus.ASSIGNED.value,
            TaskStatus.RUNNING.value,
            TaskStatus.PAUSED.value,
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value,
        ],
    )
    plan_counts = _status_counts(
        plan_statuses,
        [
            PlanStatus.DRAFT.value,
            PlanStatus.APPROVED.value,
            PlanStatus.EXECUTING.value,
            PlanStatus.COMPLETED.value,
            PlanStatus.FAILED.value,
            PlanStatus.CANCELLED.value,
        ],
    )

    worker_counts["total"] = len(workers)
    task_counts["total"] = len(tasks)
    plan_counts["total"] = len(plans)

    worker_timeout = float(getattr(registry, "heartbeat_timeout_s", 0.0) or 0.0)
    stale_workers = 0
    worker_cards: list[dict[str, Any]] = []
    for worker in sorted(workers, key=lambda item: (item.name.lower(), item.worker_id.lower())):
        heartbeat_age = max(0.0, now - float(worker.last_heartbeat or 0.0))
        is_stale = worker_timeout > 0 and heartbeat_age > worker_timeout
        stale_workers += 1 if is_stale else 0
        worker_cards.append(
            {
                "worker_id": worker.worker_id,
                "name": worker.name,
                "status": worker.status.value if hasattr(worker.status, "value") else str(worker.status),
                "capabilities": worker.capabilities,
                "current_task_id": worker.current_task_id,
                "base_url": worker.base_url,
                "heartbeat_age_s": round(heartbeat_age, 1),
                "is_stale": is_stale,
            }
        )

    worker_counts["stale"] = stale_workers

    active_statuses = {TaskStatus.ASSIGNED.value, TaskStatus.RUNNING.value, TaskStatus.PAUSED.value}
    active_tasks = [task for task in tasks if (task.status.value if hasattr(task.status, "value") else str(task.status)) in active_statuses]
    active_tasks.sort(key=lambda item: item.updated_at, reverse=True)

    active_task_cards = [
        {
            "task_id": task.task_id,
            "label": task.label or task.instruction[:72] or "Untitled task",
            "instruction_preview": task.instruction[:180],
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
            "worker_id": task.worker_id,
            "plan_id": task.plan_id,
            "progress_count": len(task.progress),
            "retry_count": task.retry_count,
            "timeout_s": task.timeout_s,
            "updated_age_s": round(max(0.0, now - float(task.updated_at or task.created_at or now)), 1),
        }
        for task in active_tasks[:6]
    ]

    plan_cards: list[dict[str, Any]] = []
    for plan in sorted(plans, key=lambda item: item.updated_at, reverse=True)[:6]:
        completed_steps = sum(1 for step in plan.steps if step.status == TaskStatus.COMPLETED)
        total_steps = len(plan.steps)
        progress_percent = int((completed_steps / total_steps) * 100) if total_steps else 0
        plan_cards.append(
            {
                "plan_id": plan.plan_id,
                "title": plan.title or plan.goal or "Untitled plan",
                "goal": plan.goal,
                "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "pending_steps": sum(1 for step in plan.steps if step.status == TaskStatus.PENDING),
                "failed_steps": sum(1 for step in plan.steps if step.status == TaskStatus.FAILED),
                "progress_percent": progress_percent,
                "step_summaries": [
                    {
                        "index": step.index,
                        "label": step.label or step.instruction[:72] or f"Step {step.index}",
                        "status": step.status.value if hasattr(step.status, "value") else str(step.status),
                    }
                    for step in plan.steps[:4]
                ],
                "updated_age_s": round(max(0.0, now - float(plan.updated_at or plan.created_at or now)), 1),
            }
        )

    observability_enabled = all(hasattr(app.state, attr) for attr in ("collector", "event_store", "sse_hub"))
    observability: dict[str, Any] = {
        "enabled": observability_enabled,
        "active_runs": 0,
        "buffer_size": 0,
        "sse_subscribers": 0,
        "total_tokens": 0,
    }
    if observability_enabled:
        collector = app.state.collector
        event_store = app.state.event_store
        sse_hub = app.state.sse_hub
        token_usage = await event_store.get_token_usage()
        observability.update(
            {
                "active_runs": len(collector.get_active_runs()),
                "buffer_size": len(getattr(collector, "_buffer", [])),
                "sse_subscribers": sse_hub.subscriber_count,
                "total_tokens": int(token_usage.get("total_tokens", 0)),
            }
        )

    runtime = _build_runtime_summary()

    return {
        "generated_at": datetime.fromtimestamp(now, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "system_status": _derive_system_status(worker_counts, task_counts),
        "worker_counts": worker_counts,
        "task_counts": task_counts,
        "plan_counts": plan_counts,
        "observability": observability,
        "workers": worker_cards,
        "active_tasks": active_task_cards,
        "recent_plans": plan_cards,
        "runtime": runtime,
        "task_queue_pressure": task_counts.get(TaskStatus.PENDING.value, 0) + task_counts.get(TaskStatus.ASSIGNED.value, 0),
        "worker_utilization_percent": int((worker_counts.get(WorkerStatus.BUSY.value, 0) / worker_counts["total"]) * 100) if worker_counts["total"] else 0,
        "links": {
            "console": "/console",
            "api_docs": "/api/docs",
            "xray_dashboard": "/dashboard" if observability_enabled else None,
        },
    }