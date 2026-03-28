# Supervisor Gateway 文档索引

本目录用于将 Supervisor Gateway 的活跃规划与已完成交付拆分管理，避免主蓝图持续膨胀。

## 文档分工

- [全局蓝图归档](SUPERVISOR_BLUEPRINT.md)
  - 保留所有 Phase 定义、优先级矩阵、实施路线的归档。由于所有 P1 特性均已上线，当前蓝图转为归档。

- [部署说明](deployment.md)
  - 说明当前代码状态下 supervisor、worker、gateway、channel 的正确启动顺序。
  - 适合排查“为什么 API 可用但 channel 不可用”这类问题。

- [Phase 0 Release Note](release-notes/phase-0-mvp.md)
  - 记录 MVP 验证阶段的交付、测试、设计决策与历史快照。

- [Phase 1 Release Note](release-notes/phase-1-production-hardening.md)
  - 记录生产加固阶段 Task 1.1 到 1.5 的交付、验证结果与收尾事项。

- [Phase 2 Release Note](release-notes/phase-2-state-persistence-and-recovery.md)
  - 记录状态持久化、任务重试与 worker 优雅关闭阶段的交付与验证结果。

- [Phase 3 Release Note](release-notes/phase-3-channel-integration.md)
  - 记录通道回传、路由策略与实时进度推送阶段的交付与验证结果。

- [Phase 4 Release Note](release-notes/phase-4-agent-loop-integration.md)
  - 记录 Agent Loop 原生委派、远程 subagent 与进程内 worker 阶段的交付与验证结果。

- [Phase 5 Release Note](release-notes/phase-5-memory-and-context.md)
  - 记录记忆与上下文共享（分布式会话、长期记忆）的交付与验证结果。

## 建议用法

- 了解全景规划及未来展望：优先阅读 [全局蓝图归档](SUPERVISOR_BLUEPRINT.md)
- 查已经做过什么、为什么这么做：进入对应 release note
- 需要整理历史上下文：先看本索引，再跳转到对应阶段文档