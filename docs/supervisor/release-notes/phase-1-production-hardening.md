# Supervisor Gateway Release Note — Phase 1 生产加固

> 发布日期：2026-03-28  
> 状态：已完成，主蓝图已切换为后续 Phase 的活跃规划。

## 目标

让 MVP 在真实环境中可靠运行，补齐监控、超时、配置与恢复能力。

## 交付摘要

- Task 1.1：X-Ray 事件发射已接入 worker、task、plan、eviction 全链路
- Task 1.2：任务超时已强制执行，watchdog 已纳入 stale task 扫描
- Task 1.3：planner 正常与异常路径已补齐单元测试
- Task 1.4：supervisor 配置 schema、CLI 默认值与覆盖链路已完成
- Task 1.5：worker 网络抖动场景的 HTTP 重试与注册恢复已完成

## Task 1.1 — X-Ray 事件发射

**已完成**：

- `registry.py` 接受可选 `collector: XRayCollector` 参数
- 关键路径事件已发射：
  - `register_worker()` → `WORKER_REGISTERED`
  - `heartbeat()` → `WORKER_HEARTBEAT`
  - `scan_unhealthy_workers()` → `WORKER_UNHEALTHY`
  - `evict_worker()` → `WORKER_EVICTED`
  - `create_task()` → `TASK_CREATED`
  - `claim_task()` → `TASK_ASSIGNED`
  - `report_progress()` → `TASK_PROGRESS`
  - `report_result(success)` → `TASK_COMPLETED`
  - `report_result(failure)` → `TASK_FAILED`
  - `cancel_task()` → `TASK_CANCELLED`
  - `create_plan()` → `PLAN_CREATED`
  - `approve_plan()` → `PLAN_APPROVED`
  - `_advance_plan(completed)` → `PLAN_COMPLETED`
  - `_advance_plan(failed)` → `PLAN_FAILED`
- 引入 `EventSink` 抽象层，隔离 supervisor 领域逻辑与 X-Ray 实现
- `claim_task()` 从全量排序优化为线性最早选择
- 任务结果事件 payload 收敛为 `result_preview + result_len`

**验证**：

- `PYTHONPATH=. pytest -q tests/test_supervisor_registry.py tests/test_xray_events.py`
- 结果：29 passed

**剩余收尾项**：

- 事件发射超时阈值 `0.05s` 仍是代码内默认值，尚未配置化

## Task 1.2 — 任务超时强制执行

**已完成**：

- `WorkerRunner._execute_task()` 增加 `asyncio.wait_for(timeout=task.timeout_s)` 包装
- 超时后统一上报 `FAILED`，错误信息为 `task timed out after {n}s`
- `registry.py` 新增 `scan_stale_tasks()`，可扫描并失败超时的 ASSIGNED/RUNNING 任务
- watchdog 现已同时检查 worker 心跳与 stale task
- plan 状态会随着 stale task 失败自动推进

**验证**：

- `PYTHONPATH=. pytest -q tests/test_supervisor_registry.py tests/test_supervisor_integration.py`
- 结果：42 passed

## Task 1.3 — Planner 单元测试

**已完成**：

- 新增 `tests/test_supervisor_planner.py`
- 覆盖场景：
  - 简单请求返回 `None`
  - 复杂请求返回多步骤 `Plan`
  - 非法 JSON 优雅降级
  - markdown 代码栅栏 JSON 可正确解析
  - 空步骤列表返回 `None`
- 已校验 `depends_on` 依赖关系保留正确

**验证**：

- `PYTHONPATH=. pytest -q tests/test_supervisor_planner.py tests/test_supervisor_registry.py tests/test_supervisor_integration.py`
- 结果：47 passed

## Task 1.4 — 配置 Schema

**已完成**：

- 新增 `SupervisorConfig`
- `Config` 顶层已接入 `supervisor: SupervisorConfig`
- supervisor CLI 以配置文件为默认来源，CLI 参数可覆盖
- supervisor task API 与 plan 调度均会继承 registry 默认任务参数

**验证**：

- API 默认值继承、显式 override、CLI 配置优先级、CLI override 已补测试

## Task 1.5 — Worker 断线恢复

**已完成**：

- `SupervisorClient` 已统一收敛到指数退避重试封装，默认最多 5 次
- 自动重试网络错误与可重试 HTTP 状态码
- `WorkerRunner` 启动注册改为循环重试，避免 supervisor 短暂不可用时直接退出
- `heartbeat` / `claim` 失败路径保持非致命

**验证**：

- 覆盖 request error 重试、可重试/不可重试 HTTP 状态、worker 注册恢复路径

## 阶段回归结果

已执行：

```bash
PYTHONPATH=. /Users/mgong/miniforge3/envs/legonanobot/bin/pytest -q \
  tests/test_worker_client.py \
  tests/test_worker_runner.py \
  tests/test_supervisor_integration.py \
  tests/test_supervisor_api.py \
  tests/test_commands.py
```

结果：81 passed

## 当前代码快照

### Supervisor 模块

```text
nanobot/supervisor/
├── __init__.py
├── app.py
├── event_sink.py
├── models.py
├── registry.py
├── planner.py
├── watchdog.py
└── api/
    ├── __init__.py
    ├── workers.py
    ├── tasks.py
    └── plans.py
```

### Worker 模块

```text
nanobot/worker/
├── __init__.py
├── client.py
└── runner.py
```

### 相关测试

```text
tests/
├── test_supervisor_models.py
├── test_supervisor_registry.py
├── test_supervisor_api.py
├── test_supervisor_integration.py
├── test_supervisor_planner.py
├── test_worker_client.py
└── test_worker_runner.py
```