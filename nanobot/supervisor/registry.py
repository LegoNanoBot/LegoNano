"""Worker registry — tracks connected workers, their tasks and health."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger

from nanobot.supervisor.models import (
    HeartbeatRequest,
    Plan,
    PlanStatus,
    PlanStep,
    Task,
    TaskClaimRequest,
    TaskProgressReport,
    TaskResultReport,
    TaskStatus,
    WorkerInfo,
    WorkerRegisterRequest,
    WorkerStatus,
)


class WorkerRegistry:
    """In-memory registry of workers, tasks and plans.

    Thread-safety: all mutations go through a single asyncio.Lock so that
    concurrent FastAPI handlers don't race.
    """

    def __init__(self, heartbeat_timeout_s: float = 120.0) -> None:
        self._lock = asyncio.Lock()
        self._workers: dict[str, WorkerInfo] = {}
        self._tasks: dict[str, Task] = {}
        self._plans: dict[str, Plan] = {}
        self.heartbeat_timeout_s = heartbeat_timeout_s

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    async def register_worker(self, req: WorkerRegisterRequest) -> WorkerInfo:
        async with self._lock:
            now = time.time()
            worker = WorkerInfo(
                worker_id=req.worker_id,
                name=req.name,
                capabilities=list(req.capabilities),
                base_url=req.base_url,
                registered_at=now,
                last_heartbeat=now,
            )
            self._workers[req.worker_id] = worker
            logger.info("Worker registered: {} ({})", req.worker_id, req.name)
            return worker

    async def heartbeat(self, req: HeartbeatRequest) -> WorkerInfo | None:
        async with self._lock:
            worker = self._workers.get(req.worker_id)
            if worker is None:
                return None
            worker.last_heartbeat = time.time()
            worker.current_task_id = req.current_task_id
            if req.status != WorkerStatus.OFFLINE:
                worker.status = req.status
            return worker

    async def unregister_worker(self, worker_id: str) -> bool:
        async with self._lock:
            worker = self._workers.pop(worker_id, None)
            if worker is None:
                return False
            # Release any assigned tasks back to pending
            for task in self._tasks.values():
                if task.worker_id == worker_id and task.status in (
                    TaskStatus.ASSIGNED,
                    TaskStatus.RUNNING,
                ):
                    task.status = TaskStatus.PENDING
                    task.worker_id = None
                    task.assigned_at = None
                    task.updated_at = time.time()
            logger.info("Worker unregistered: {}", worker_id)
            return True

    async def list_workers(self) -> list[WorkerInfo]:
        async with self._lock:
            return list(self._workers.values())

    async def get_worker(self, worker_id: str) -> WorkerInfo | None:
        async with self._lock:
            return self._workers.get(worker_id)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def create_task(self, task: Task) -> Task:
        async with self._lock:
            self._tasks[task.task_id] = task
            logger.info("Task created: {} ({})", task.task_id, task.label or task.instruction[:40])
            return task

    async def claim_task(self, req: TaskClaimRequest) -> Task | None:
        """Find the oldest pending task the worker can handle and assign it."""
        async with self._lock:
            worker = self._workers.get(req.worker_id)
            if worker is None:
                return None
            # Simple FIFO: pick the first pending task
            for task in sorted(self._tasks.values(), key=lambda t: t.created_at):
                if task.status != TaskStatus.PENDING:
                    continue
                task.status = TaskStatus.ASSIGNED
                task.worker_id = req.worker_id
                task.assigned_at = time.time()
                task.updated_at = time.time()
                worker.status = WorkerStatus.BUSY
                worker.current_task_id = task.task_id
                logger.info("Task {} claimed by worker {}", task.task_id, req.worker_id)
                return task
            return None

    async def report_progress(self, rpt: TaskProgressReport) -> Task | None:
        async with self._lock:
            task = self._tasks.get(rpt.task_id)
            if task is None or task.worker_id != rpt.worker_id:
                return None
            from nanobot.supervisor.models import TaskProgress

            task.progress.append(TaskProgress(
                iteration=rpt.iteration,
                message=rpt.message,
                data=dict(rpt.data),
            ))
            task.status = TaskStatus.RUNNING
            task.updated_at = time.time()
            return task

    async def report_result(self, rpt: TaskResultReport) -> Task | None:
        async with self._lock:
            task = self._tasks.get(rpt.task_id)
            if task is None or task.worker_id != rpt.worker_id:
                return None
            task.status = rpt.status
            task.result = rpt.result
            task.error = rpt.error
            task.updated_at = time.time()

            # Free the worker
            worker = self._workers.get(rpt.worker_id)
            if worker:
                worker.status = WorkerStatus.ONLINE
                worker.current_task_id = None

            logger.info("Task {} result: {}", rpt.task_id, rpt.status.value)

            # Advance plan if task belongs to one
            if task.plan_id:
                await self._advance_plan_unlocked(task.plan_id)

            return task

    async def cancel_task(self, task_id: str) -> Task | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                return task
            task.status = TaskStatus.CANCELLED
            task.updated_at = time.time()
            # Free the worker
            if task.worker_id:
                worker = self._workers.get(task.worker_id)
                if worker and worker.current_task_id == task_id:
                    worker.status = WorkerStatus.ONLINE
                    worker.current_task_id = None
            return task

    async def get_task(self, task_id: str) -> Task | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        plan_id: str | None = None,
    ) -> list[Task]:
        async with self._lock:
            tasks = list(self._tasks.values())
            if status is not None:
                tasks = [t for t in tasks if t.status == status]
            if plan_id is not None:
                tasks = [t for t in tasks if t.plan_id == plan_id]
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    async def create_plan(self, plan: Plan) -> Plan:
        async with self._lock:
            self._plans[plan.plan_id] = plan
            logger.info("Plan created: {} ({})", plan.plan_id, plan.title)
            return plan

    async def get_plan(self, plan_id: str) -> Plan | None:
        async with self._lock:
            return self._plans.get(plan_id)

    async def list_plans(self, status: PlanStatus | None = None) -> list[Plan]:
        async with self._lock:
            plans = list(self._plans.values())
            if status is not None:
                plans = [p for p in plans if p.status == status]
            return sorted(plans, key=lambda p: p.created_at, reverse=True)

    async def approve_plan(self, plan_id: str) -> Plan | None:
        """Approve a draft plan and create tasks for ready steps."""
        async with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None or plan.status != PlanStatus.DRAFT:
                return plan
            plan.status = PlanStatus.APPROVED
            plan.updated_at = time.time()
        # Create tasks for steps whose dependencies are met (outside lock)
        await self._schedule_ready_steps(plan_id)
        return await self.get_plan(plan_id)

    async def cancel_plan(self, plan_id: str) -> Plan | None:
        async with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            plan.status = PlanStatus.CANCELLED
            plan.updated_at = time.time()
            # Cancel all pending/running tasks in this plan
            for task in self._tasks.values():
                if task.plan_id == plan_id and task.status in (
                    TaskStatus.PENDING,
                    TaskStatus.ASSIGNED,
                    TaskStatus.RUNNING,
                ):
                    task.status = TaskStatus.CANCELLED
                    task.updated_at = time.time()
            return plan

    async def _schedule_ready_steps(self, plan_id: str) -> None:
        """Create tasks for plan steps whose dependencies are satisfied."""
        async with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None or plan.status not in (PlanStatus.APPROVED, PlanStatus.EXECUTING):
                return

            completed_indices: set[int] = set()
            for step in plan.steps:
                if step.status == TaskStatus.COMPLETED:
                    completed_indices.add(step.index)

            for step in plan.steps:
                if step.task_id is not None or step.status != TaskStatus.PENDING:
                    continue
                if all(dep in completed_indices for dep in step.depends_on):
                    task = Task(
                        plan_id=plan_id,
                        step_index=step.index,
                        instruction=step.instruction,
                        label=step.label or f"Plan {plan_id} step {step.index}",
                        origin_channel=plan.origin_channel,
                        origin_chat_id=plan.origin_chat_id,
                        session_key=plan.session_key,
                    )
                    self._tasks[task.task_id] = task
                    step.task_id = task.task_id
                    logger.info(
                        "Scheduled step {} of plan {} → task {}",
                        step.index, plan_id, task.task_id,
                    )

            if plan.status == PlanStatus.APPROVED:
                plan.status = PlanStatus.EXECUTING
                plan.updated_at = time.time()

    async def _advance_plan_unlocked(self, plan_id: str) -> None:
        """Check plan completion after a task finishes. Must be called under _lock."""
        plan = self._plans.get(plan_id)
        if plan is None:
            return

        # Sync step status from tasks
        for step in plan.steps:
            if step.task_id:
                task = self._tasks.get(step.task_id)
                if task:
                    step.status = task.status
                    if task.result:
                        step.result_summary = task.result[:500]

        all_done = all(
            s.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
            for s in plan.steps
        )
        any_failed = any(s.status == TaskStatus.FAILED for s in plan.steps)

        if any_failed:
            plan.status = PlanStatus.FAILED
            plan.updated_at = time.time()
        elif all_done:
            plan.status = PlanStatus.COMPLETED
            plan.updated_at = time.time()

    # ------------------------------------------------------------------
    # Health scanning
    # ------------------------------------------------------------------

    async def scan_unhealthy_workers(self) -> list[WorkerInfo]:
        """Mark workers whose heartbeat is overdue as unhealthy and return them."""
        now = time.time()
        unhealthy: list[WorkerInfo] = []
        async with self._lock:
            for w in self._workers.values():
                if w.status == WorkerStatus.OFFLINE:
                    continue
                if now - w.last_heartbeat > self.heartbeat_timeout_s:
                    w.status = WorkerStatus.UNHEALTHY
                    unhealthy.append(w)
        return unhealthy

    async def evict_worker(self, worker_id: str) -> list[Task]:
        """Remove an unhealthy worker and reassign its tasks back to pending."""
        reassigned: list[Task] = []
        async with self._lock:
            worker = self._workers.pop(worker_id, None)
            if worker is None:
                return reassigned
            for task in self._tasks.values():
                if task.worker_id == worker_id and task.status in (
                    TaskStatus.ASSIGNED,
                    TaskStatus.RUNNING,
                ):
                    task.status = TaskStatus.PENDING
                    task.worker_id = None
                    task.assigned_at = None
                    task.updated_at = time.time()
                    reassigned.append(task)
            logger.warning("Evicted worker {} — {} tasks re-queued", worker_id, len(reassigned))
        return reassigned
