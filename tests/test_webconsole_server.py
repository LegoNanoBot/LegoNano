"""Tests for the phase-1 WebConsoleServer pages and summary API."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from nanobot.WebConsoleServer import api as webconsole_api
from nanobot.supervisor.app import create_supervisor_app
from nanobot.supervisor.models import Plan, PlanStep, Task, TaskClaimRequest, TaskStatus, WorkerRegisterRequest
from nanobot.supervisor.registry import WorkerRegistry


@pytest.mark.asyncio
async def test_webconsole_summary_collects_supervisor_state():
    registry = WorkerRegistry(heartbeat_timeout_s=60.0)

    await registry.register_worker(
        WorkerRegisterRequest(worker_id="w1", name="Alpha", capabilities=["code", "review"])
    )
    task = await registry.create_task(Task(instruction="Run checks", label="Check queue"))
    await registry.claim_task(TaskClaimRequest(worker_id="w1", capabilities=[]))
    plan = Plan(title="Console rollout", goal="Ship phase-1", steps=[PlanStep(index=0, instruction="Build UI")])
    await registry.create_plan(plan)

    app = create_supervisor_app(worker_registry=registry)
    with TestClient(app) as client:
        response = client.get("/api/v1/webconsole/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["worker_counts"]["total"] == 1
    assert data["task_counts"][TaskStatus.ASSIGNED.value] == 1
    assert data["plan_counts"]["total"] == 1
    assert data["workers"][0]["name"] == "Alpha"
    assert data["active_tasks"][0]["task_id"] == task.task_id
    assert data["active_tasks"][0]["instruction_preview"] == "Run checks"
    assert data["recent_plans"][0]["goal"] == "Ship phase-1"


def test_webconsole_root_redirects_to_console():
    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/console"


def test_webconsole_page_renders_phase1_dashboard():
    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.get("/console")

    assert response.status_code == 200
    assert "System Console" in response.text
    assert "Interactive Controls" in response.text
    assert "Launch A Quick Task" in response.text
    assert "Filter Live Overview" in response.text
    assert "Worker Matrix" in response.text
    assert "Managed Components" in response.text
    assert "/console-assets/webconsole.css?v=" in response.text


def test_webconsole_summary_includes_runtime_component_status(monkeypatch, tmp_path):
    pid_dir = tmp_path / "pids"
    log_dir = tmp_path / "logs"
    pid_dir.mkdir()
    log_dir.mkdir()
    (pid_dir / "nanobot-gateway.pid").write_text(str(os.getpid()), encoding="utf-8")
    (pid_dir / "nanobot-supervisor.pid").write_text("999999", encoding="utf-8")

    monkeypatch.setenv("NANOBOT_PID_DIR", str(pid_dir))
    monkeypatch.setenv("NANOBOT_LOG_DIR", str(log_dir))

    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.get("/api/v1/webconsole/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime"]["counts"]["running"] == 1
    assert data["runtime"]["counts"]["stale"] == 1
    assert data["runtime"]["components"][0]["name"] == "gateway"
    assert data["runtime"]["components"][1]["state"] == "stale"


def test_webconsole_stream_exposes_sse_updates():
    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        with client.stream("GET", "/console/stream?interval_s=0.1&max_updates=1") as response:
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line)
                if len(lines) >= 2:
                    break

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert any("event: overview" in line for line in lines)


def test_webconsole_quick_create_task_creates_registry_task():
    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/webconsole/tasks/quick-create",
            json={"label": "UI task", "instruction": "Inspect the queue"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["task"]["label"] == "UI task"
    assert data["message"].startswith("Task ")


@pytest.mark.asyncio
async def test_webconsole_control_runtime_status_returns_script_output(monkeypatch):
    async def fake_run_script(script_name: str):
        return {
            "script": script_name,
            "returncode": 0,
            "stdout": "runtime healthy",
            "stderr": "",
        }

    monkeypatch.setattr(webconsole_api, "_run_script", fake_run_script)

    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.post("/api/v1/webconsole/control/runtime/status")

    assert response.status_code == 200
    data = response.json()
    assert data["scheduled"] is False
    assert "runtime healthy" in data["message"]


@pytest.mark.asyncio
async def test_webconsole_control_supervisor_restart_schedules_background_action(monkeypatch):
    scheduled = {"called": False}

    async def fake_schedule(scripts: list[str]):
        scheduled["called"] = True
        assert scripts == ["stop-supervisor.sh", "start-supervisor.sh"]

    monkeypatch.setattr(webconsole_api, "_schedule_disruptive_action", fake_schedule)

    app = create_supervisor_app(worker_registry=WorkerRegistry())
    with TestClient(app) as client:
        response = client.post("/api/v1/webconsole/control/supervisor/restart")

    assert response.status_code == 200
    data = response.json()
    assert data["scheduled"] is True
    assert scheduled["called"] is True