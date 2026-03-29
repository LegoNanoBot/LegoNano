# LegoNanoBot - 下一代产品设计与迭代文档 (PRD & Roadmap)

## 1. 概述与核心定位 (Product Overview & Positioning)

### 1.1 产品背景
当前 LegoNanoBot 是基于港大 `nanobot` 基础上的增强版本。随着业务复杂度的增加以及多智能体协作(Multi-Agent)概念的发展，系统当前的 CLI/配置文件 操作模式已呈现瓶颈。参考业界顶尖平台（如 OpenAkita），我们期望将其重塑为一个**乐高式的插件化智能体操作平台**，赋予其动态的可视化能力、分布式监督(Supervisor)管理能力，并最终迈向面向 Serverless 等云原生的部署形态。

### 1.2 问题陈述 (Problem Statement)
* **扩展面临痛点**：用户在变更 LLM 服务商 (Provider)、通信渠道 (Channel)、记忆库 (Memory) 时体验割裂，无法达成像积木一样“即插即用”的效果。
* **黑盒运行与管理缺失**：多个 nanobot worker 同时工作时缺乏集中的视图与追踪，难以进行资源分配、配置热更新、异常重启和任务手动下拨。
* **部署受限**：系统目前的常驻运行模型（Polling机制）无法完全适应如 AWS Lambda 等按调用次数计费的云端 Serverless 架构，且缺乏分布式数据库支撑。

### 1.3 成功指标 (Success Metrics)
* **易用率**：新手用户可以在不修改任何代码的情况下，纯粹在可视化控制面板上完成首个由不同插件拼装的 NanoBot 的启动。
* **高可用性设计度**：`provider`、`channel`、`memory` 达到 100% 独立插件化标准。主工程对扩展修改保持“封闭”，仅通过注册机制挂载。
* **网关吞吐量**：Supervisor UI 能够实时且稳定地透视至少超过10个以上并发运行的 Workers 的 X-Ray 日志以及处理在线任务指派。

---

## 2. 核心架构设计理念 (Core Architecture Design)

以 **"微内核调度 + 插件生态边界 + 可视化协作网关"** 为设计骨架：

1. **原子级核心扩展点（Lego-like Plugins）**
   实施严格的工厂协议接口。核心不关心如何建立聊天或者如何调用大模型——全部下放。允许系统随时在运行时扫描插件目录或载入第三方 ZIP 模块扩展 `Memory`、`Provider`、`Channel`。云端组件本质是遵守此接口挂载的远端插件。
2. **监督与网关系统（Supervisor System）**
   作为所有多 Workers 的"大脑"。Supervisor 进程维护所有 Worker 的状态机：存活状态（Heartbeat检查）、活跃载荷、指令队列缓冲池。所有前端面板交互只需和 Supervisor 发生 API 请求对接。
3. **可视化呈现层（Web Control Panel & X-Ray）**
   采用前后端分离独立服务（React/Vue 3）。功能主轴拆分为：面向组合的 **节点拓扑配装（Node-Based）**、面向运维的 **Worker监控矩阵** 及面向调试的 **X-Ray实时日志全链路视图**。
4. **云原生包容方案（Cloud-Native Ready）**
   通过设计“无状态”原则，将所有的会话上下文强依赖剥离至外置 Memory 组件（如 Postgres 插件）。针对轮询类的 Channel 提供 Webhook 被动触发层（Adapter），实现生命周期函数化以适配云函数架构。

---

## 3. 功能需求详细说明 (Feature Requirements)

### 3.1 乐高式高阶插件化系统 (Dynamic Plugin System) [P0]
* **价值阐述**：实现类似 VSCode 的快速扩展生态，极速适配各种新型 LLM 或私有领域社交软件。
* **主要特性**：
  * **统一规范（Manifest）**：制定 `nano_plugin.yaml` 声明文件规范，定义元数据、入口点与依赖参数。
  * **在线热插拔流**：实现动态重载器，在不影响系统主干和在线 Worker 的情况下激活或下线新模块插件。
  * **Schema 动态配置提取**：所有的插件内置 Pydantic/JSONSchema。使前端在用户选择某一插件时，自适应生成填写表单予以配置。

### 3.2 可视化控制级中心 (Web Control Panel) [P0]
* **功能描述**：
  * **全局总览仪表盘 (Dashboard)**：显示在线 Worker 数量分布、各类 Provider 的日均算力请求耗时、消息吞吐统计。
  * **X-RAY 日志追踪流**：提供WebSocket驱动的双向视图流。通过树状/瀑布图形式追溯一次事件完整生命周期（Channel 接收 -> Memory读取/归档 -> Provider思考步骤 -> Skills/Tool 调用）。
  * **Worker 编排与热配**：表单或看板形式一键启停各个实例（Start/Stop/Restart）；支持无缝重载其 `config` 不掉线。
  * **在线下发指令与覆盖 (Task Directives)**：允许用户通过界面直接扮演“上帝视角”，给指定的特定 Worker 推送自定义指令、手动初始化强制记忆，执行人为介入 (Human-in-the-loop)
  * **节点拼装向导**：类似工作流系统界面，可以拉拽拼装不同的 Channel 和 Provider 到一个实例上启动它。

### 3.3 管理与路由组件 Supervisor Gateway [P0]
* **当前状态**：已经完成 Phase 0 到 Phase 5 基础网关构建测试（位于 `docs/supervisor/`），现向可视化后端升级。
* **赋能模块**：
  * **标准化 Open APIs**：向前端 Dashboard 暴露完整的 RESTful / GraphQL 查询接口。
  * **路由与心跳收集**：提供 Worker 端强韧的心跳接入，将宕机实例标识报警并支持自动按规则重拉起。
  * **统一任务下发系统**：管理外部系统下达的统一任务。支持发向“所有的Worker”、“特指频道Worker”或“带有特定 Tag 的群集”。

### 3.4 远端适配与云扩展计划 [P1]
* **功能迭代**：
  * **云级 Memory 插件 (PostgreSQL etc.)**：开发针对强一致性多并发业务的分布式记忆扩展，完全替代本地单文件 Sqlite 束缚。同时支持基于插件化架构实现 **3-Layer Memory (工作区+核心持久区+动态检索向量区)**，让不同的记忆层级也能实现自由拼接和云端存储。
  * **Serverless Executor 模式支持**：开发专配的“端点模式(Endpoint Executor)”，打通基于 HTTP 请求的完整代理链路单次激发并销毁能力。未来以范例库给出云函数部署方式（Terraform/Serverless Framework 模板）。

### 3.5 自我进化与系统运行时安全 (Self-Evolution & Runtime Safety) [P1]
* **功能迭代**：
  * **依托 X-RAY + Skills 架构**：通过深度结合底层上报的 **X-RAY** 遥测数据总线，以及强大的 **Skills** 扩展生态，实现自我进化：由专门的自我反思 Skill 定期读取 X-Ray 脱敏日志，进行自动化评估与错误归因（Self-Evolution）。
  * **拦截器验证与资源阈值管控**：结合 X-RAY 实时分析流，专门的安全 Supervisor Skill 会在敏感工具调用前介入，进行确权拦截 (Human-in-the-loop)、预防工具死循环调用 (Tool thrashing)，以及计算并限制 Token / 预算开销 (Budget Limiting)。


---

## 4. 致前端设计与交互团队指引 (UX & UI Guidelines)

* **产品气质**：现代极客、极简主义，对标：Vercel、OpenAkita、Langflow。必须默认且全局全量适配 **Dark Mode（深色模式）** 以符合开发者审美偏好。
* **页面视图结构建议**：
  1. **乐高工程车间 (Plugin Studio)**：建议采用类似无代码(No-Code)蓝图方式，左侧列列出库内所有支持的 `provider`, `memory`, `channel` 型组件，右侧展示组合连接状况与当前生成的 Bot 实例抽象卡片。
  2. **终端群集监控 (Worker Fleet)**：建议采用数据矩阵或列表，直观体现每一个进程的健康指示灯(Green/Red/Archived)、CPU/内存表现，以及当前配置参数悬浮窗。
  3. **实时沙盒测试台 (X-Ray Sandbox)**：该视图左侧为用户与Bot的模拟输入框和手动任务派发框。右侧为类似Chrome控制台Network面板的可展开堆栈(Stack)，供剖析系统推理或API报错链路。

---

## 5. 项目路线图与里程碑规划 (Agile Roadmap)

基于系统复杂度评估，按 Sprint 迭代排期（RICE 优先级驱动）：

### 第一阶段 (Milestone 1)：重构与基础打通 (期望: 2个 Sprint)
* **架构演进**：完善并冻结 Plugin 动态挂载协议与 JSONSchema 向配置系统反射的能力。开放并完善 Supervisor 需要的前后端对接 GraphQL/REST 接口。
* **前端实现**：控制面板基建完成。实现"系统 Dashboard"，"插件配置自动渲染表单" 与 "最基础版本的 Worker 一键启停功能"。

### 第二阶段 (Milestone 2)：控制台纵深闭环 (期望: 3个 Sprint)
* **核心发力点 -- 观测与控制**
* **架构演进**：完成 Webhook / WebSocket 的双工建立，让 Supervisor 可以将流式的 X-RAY Debug 数据分流导给浏览器；实现上帝视角的在线打断与特定任务下发路由逻辑。
* **前端实现**：完成结构复杂的 **X-RAY 日志追踪视图** 与 **沙盒模拟/人工干预页面**，极大提升项目实战时的纠错与演练体验。

### 第三阶段 (Milestone 3)：迈向云端与 Serverless (期望: 2个 Sprint)
* **业务演进**：推出可真正商用的强并发云形态。
* **架构团队**：稳定产出基于 PostgreSQL 或主流 VectorDB 规范的 Cloud Memory Plugin；抽离代码核心实现彻底无状态的云函数入口（Lambda Adapter）及完整的 Terraform IaaC 预设模板，真正实现在 AWS 级别组件中的降本增效运行。

---
> **注**: 产品文档将作为生命周期长期演进与维护文件（Living Document）。执行团队请根据实际可用资源与技术选型预研，对以上范围进行迭代拆分。
