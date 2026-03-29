# WebConsoleServer Phase 1

## Summary

本阶段交付一个最小可用的网页入口页，用于从浏览器查看 LegoNanoBot 当前系统整体状态。

实现遵循以下约束：

- 复用现有 supervisor FastAPI 服务，而不是新增独立前端工程
- 默认深色风格，优先服务开发者观测场景
- 保持移动端可读，在窄屏下自动转为堆叠布局
- 先解决“可看见整体状态”，不提前引入复杂控制流和详情页体系

## Delivered Scope

Phase-1 当前已交付：

- `/console` 系统入口页
- `/api/v1/webconsole/summary` 汇总接口
- `/console/stream` SSE 实时刷新通道
- Worker Fleet、Task Queue、Plan Engine、Observability、Runtime 五类总览卡片
- Worker Matrix、Managed Components、Active Tasks、Recent Plans 四个核心面板
- 脚本管理组件状态检测：gateway、supervisor、worker pidfile + 进程存活检查
- SSE 失败后的前端轮询回退

## Design Decisions

### Why SSR First

当前仓库已经具备 FastAPI、Jinja2、StaticFiles 和 X-Ray 页面能力。Phase-1 的核心目标只是提供统一入口页，因此直接挂载在 supervisor 服务内可以最短路径交付，并复用现有认证边界、部署方式和运行脚本。

### Why WebConsoleServer Module

网页管理能力被集中到 `nanobot/WebConsoleServer/` 下，避免把控制台逻辑散落到 supervisor API、X-Ray 页面或旧的错误前端残留中。这样后续扩展详情页、控制动作和更细粒度交互时，边界会更清晰。

### Why Snapshot + SSE

Phase-1 的数据模型以 supervisor 内存态和脚本运行态快照为主。SSE 用于定时推送最新 overview HTML，成本低、实现简单，同时又比纯轮询更适合控制台类页面。为保证稳定性，前端保留轮询回退路径。

## Routes

| Route | Purpose |
|-------|---------|
| `/` | 302 重定向到 `/console` |
| `/console` | 主控制台页面 |
| `/console/partials/overview` | 控制台 overview 局部片段 |
| `/console/stream` | SSE 概览更新流 |
| `/api/v1/webconsole/summary` | JSON 汇总接口 |

## Runtime Model

页面数据来自两类来源：

1. supervisor registry 内存态
   - workers
   - tasks
   - plans

2. 本地脚本运行态
   - `pids/` 下的 pid 文件
   - `os.kill(pid, 0)` 的进程存活检查
   - `logs/` 目录路径展示

当 X-Ray collector、event store、SSE hub 挂载到 supervisor 时，页面也会显示 observability 摘要。

## Local Runbook

推荐使用仓库脚本启动：

```bash
./sbin/start-supervisor.sh
./sbin/start-nanobot.sh
./sbin/nanobot-status.sh
```

访问入口：

```text
http://127.0.0.1:9200/console
```

API 自检：

```bash
curl http://127.0.0.1:9200/api/v1/webconsole/summary
```

## Verification

聚焦验证命令：

```bash
PYTHONPATH=. pytest -q tests/test_webconsole_server.py tests/test_supervisor_api.py
```

当前测试覆盖：

- summary API 汇总 supervisor 状态
- 根路径重定向到 `/console`
- 页面 SSR 渲染成功
- runtime component 状态识别
- SSE 流可返回 overview 事件

## Known Gaps

以下内容不在 phase-1 范围内：

- 网页内 Start / Stop / Restart 按钮
- Worker / Task / Plan 详情页
- 基于真实事件源的增量更新，而不是定时快照
- 独立前端工程、节点编排画布和插件工作台

## Follow-up Candidates

后续可以按以下顺序扩展：

1. 在 Managed Components 面板增加安全的控制按钮
2. 为 Worker、Task、Plan 增加详情页和 drill-down 能力
3. 把 SSE 从“定时快照”升级为“真实事件驱动更新”
4. 为控制台补充鉴权和操作审计