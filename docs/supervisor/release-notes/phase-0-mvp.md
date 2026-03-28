# Supervisor Gateway Release Note — Phase 0 MVP 验证

> 发布日期：2026-03-26  
> 状态：已完成，详细实现已归档到本文件。

## 目标

最小可行产品，验证 Supervisor Gateway 核心架构可跑通。

## 已交付内容

| 模块 | 文件 | 行数 | 状态 |
|------|------|------|------|
| 数据模型 | `nanobot/supervisor/models.py` | ~192 | ✅ |
| 注册表 | `nanobot/supervisor/registry.py` | ~350 | ✅ |
| 计划器 | `nanobot/supervisor/planner.py` | ~130 | ✅ |
| 看门狗 | `nanobot/supervisor/watchdog.py` | ~70 | ✅ |
| FastAPI 应用 | `nanobot/supervisor/app.py` | ~90 | ✅ |
| API: Workers | `nanobot/supervisor/api/workers.py` | ~115 | ✅ |
| API: Tasks | `nanobot/supervisor/api/tasks.py` | ~200 | ✅ |
| API: Plans | `nanobot/supervisor/api/plans.py` | ~130 | ✅ |
| Worker 客户端 | `nanobot/worker/client.py` | ~130 | ✅ |
| Worker 运行器 | `nanobot/worker/runner.py` | ~350 | ✅ |
| CLI 命令 | `nanobot/cli/commands.py` | +135 | ✅ |
| X-Ray 事件类型 | `nanobot/xray/events.py` | +14 常量 | ✅ |

## 测试结果

- 58 单元测试 + 13 集成测试 = 71 新测试
- 当时全套测试 441 通过

## 设计决策

- 内存态注册表：`dict + asyncio.Lock`
- 任务调度：朴素 FIFO
- Worker 通信模式：主动 poll
- 计划模型：DAG 依赖跟踪
- 失败策略：任务失败即计划失败
- 集成测试：`httpx.ASGITransport` 进程内联调

## 阶段性限制快照

以下限制是在 Phase 0 完成时的历史状态，其中部分已在 Phase 1 中解决：

- 任务超时字段定义但未强制执行
- 注册表纯内存，重启即丢
- 无通道回传
- 无认证机制
- planner 无单元测试
- 无配置 schema
- worker 无重连/断线恢复

## 后续衔接

- 以上“任务超时 / planner 单测 / 配置 schema / worker 重连”已在 Phase 1 完成
- 注册表持久化、通道回传、安全认证仍在后续蓝图内推进