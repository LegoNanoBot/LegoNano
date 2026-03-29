# LegoNanoBot - 下一代 UI/UX 设计指导说明原则 (UI/UX Design Guidelines)

## 1. 概述与设计愿景 (Overview & Vision)
LegoNanoBot 正在向一个**乐高式的插件化多智能体操作平台**演进。系统不仅提供零门槛的新手接入体验，同时为极客和开发者提供极其深度的系统“透视”与“编排”能力。
**设计主旨**：把复杂的 Multi-Agent 架构和冗长的执行日志，转化为直观、可控、如拼装乐高般愉悦的交互体验。

**对标竞品/灵感来源**：
* 布局与极简感：**Google Workspace**、**Gmail**、**Google Cloud Console**
* 节点拓扑与画布交互：**Langflow**、**ComfyUI**
* 开发者日志诊断：**Chrome DevTools (Network 视图)**、**DataDog**
* 组件语言与图标：**Material 3**、**Material Symbols Rounded**

---

## 2. 设计语言与系统基调 (Design Language)

### 2.1 风格定调：Google Friendly, Light-First (Google 亲和风格，浅色优先)
* **目标受众**：面向开发者、运营者及 AI 训练师，但视觉基调不再走“压迫感深色极客风”。默认使用**浅色主题**，并提供更柔和的 Dark Theme 作为可选项。
* **视觉感受**：参考 Gmail / Google Cloud Console 的层级关系，强调清晰留白、圆角卡片、温和阴影、明确的语义色块，减少大面积纯黑背景。
* **语义色彩**：
  * **🟢 运行正常 (Healthy)**：Google Green `#34A853`
  * **🟡 等待/挂起 (Pending)**：Google Yellow `#FBBC04` / Amber `#F9AB00`
  * **🔴 异常/报错 (Error)**：Google Red `#EA4335`
  * **🔵 主操作 / 关键入口 (Primary)**：Google Blue `#1A73E8`
* **深色模式要求**：Dark Theme 仅作为补充主题，不得牺牲亲和感；背景使用深灰而不是纯黑，状态色需降低刺眼程度并保留足够可读性。

### 2.2 字体与排版 (Typography)
* **系统字体**：优先采用 Google 风格字体栈，如 `Google Sans` / `Roboto` / `Helvetica Neue`。
* **等宽字体 (Monospace)**：用于所有的代码块、日志、X-Ray Trace ID 和 JSON Schema 输出 (推荐：`Roboto Mono`, `JetBrains Mono`)。
* **信息层级**：通过字重(Weight)和灰度明暗(Opacity)而非字号差异来构建复杂的参数表单层级。

### 2.3 图标语言 (Iconography)
* **统一图标体系**：整体 icon 选择必须向 Google 系靠拢，优先使用 **Material Symbols Rounded / Outlined**。
* **交互原则**：图标与文本并列出现时，图标用于快速识别功能分区，不替代文字本身；避免炫技式抽象图标。
* **风格要求**：控制台、表单、导航、状态提示统一保持 Gmail/Google Workspace 那种轻量、圆角、线性轮廓感。

---

## 3. 核心视图布局设计建议 (Core View Layouts)

### 3.1 零门槛部署引导页 (Zero-Barrier Setup Wizard)
* **场景**：用户首次安装或初始化一个全新 Bot。
* **设计原则**：**极其克制、单线程操作**。全屏聚焦(Focus Mode)，移除侧边栏。引导采用分步式 (Step 1: API Key -> Step 2: 选择 Channel -> Step 3: 赋予 Persona)。
* **要求**：微动效加持（如对接成功时的“点亮”连线动画），让硬核的配置过程具有“开箱即用”的游戏感。

### 3.2 全局仪表盘与终端群集 (Dashboard & Worker Fleet)
* **场景**：统览当前主机上运行的所有 Bot Worker 状态。
* **视图建议**：
  * **数据矩阵/卡片流**：每一个运行的 Bot 是一个 Google 风格卡片。卡片内必须包含：头像/名字、🟢状态灯、当前 Provider、当前任务、必要时可加简化活跃度可视化。
  * **控制区**：卡片或列表行内直接暴露 `Start / Stop / Restart / Inspect` 等操作，交互反馈应在前端即时出现，避免用户跳转到 CLI。
  * **信息组织**：优先使用 Chip、Badge、Inline Action 的组合，而不是厚重边框和霓虹发光效果。

### 3.3 乐高工程车间 (Node-Based Plugin Studio)
* **场景**：高级用户拼接 Channel、Provider 和 3-Layer Memory 模块。
* **视图建议（三栏布局）**：
  * **左侧**：插件仓库库 (Components Library)，按颜色或类型归类的可拖拽节点。
  * **中间主画布 (Canvas)**：无代码连线区域，用户在此处拼装“大脑(Provider)”、“躯干(Memory)”与“触手(Channel/Skills)”。
  * **右侧**：**动态属性面板 (Dynamic Property Panel)**。前端会接收后端的 JSONSchema，在此处自动渲染出表单（输入框、开关、下拉菜单）。设计时必须考虑表单极长、嵌套对象和数组项的折叠/展开等优雅交互。

### 3.4 实时沙盒与 X-Ray 透视台 (X-Ray Sandbox) [⭐最核心页面]
* **场景**：在线调试、查看大模型推理链路（Chain-of-thought）及监控 Runtime 安全拦截。
* **视图建议（极客双栏模式）**：
  * **左栏 (C2C 交互模拟器)**：普通的类似微信/Telegram的聊天界面，用于发送测试 Prompt 或下发上帝指令。同时包含 Plan Mode 下的浮动执行进度条 (Floating Progress Bar)。
  * **右栏 (深层透视堆栈 Stack)**：类似 Chrome Network 面板的**时间线/瀑布流 (Waterfall)** 视图。以树状图展开展示：`接收请求 -> 触发记忆检索(Core+Working) -> 触发拦截器(Safety) -> 大模型思考流(Deep Thinking) -> Skill工具调用 -> 输出`。
  * **动效要求**：左侧打字机流式输出时，右侧的树状节点需实时闪烁或高亮正在执行的步骤。

### 3.5 交互式控制工作台 (Interactive Control Workbench)
* **场景**：运维人员或高级用户需要直接在前端控制系统。
* **必须具备的能力**：
  * 一键刷新运行态、查看 runtime status。
  * 发起 Gateway / Supervisor / Cluster 的启停或重启动作。
  * 在前端直接快速提交任务 (Quick Task Composer)。
  * 对计划执行 `Approve / Cancel`，对任务执行 `Cancel`。
* **反馈方式**：所有控制动作都必须有前端可见的反馈区，例如 Activity Feed、Toast、状态条，而不是只在后端日志里成功。

---

## 4. 关键交互原则 (Interaction Principles)

1. **高频数据的性能降级与虚拟化**
   * X-Ray 日志可能在 1 秒内推入百条数据。设计组件时默认需支持**虚拟列表 (Virtual Scrolling)**，杜绝页面抖动卡顿。
   * 新消息/日志到底部时，应自带“钉住 (Pin to bottom)”按钮。
2. **Schema-Driven 统一表单视觉**
   * 必须基于 JSON Schema 设计一套覆盖全部输入形态的“表单组件库”（如：String、Number、Enum、Array of Objects）。因为这些配置项都是按插件动态生成的。
3. **上帝之手 (Human-in-the-loop)**
   * 当安全引擎触发（如面临危险命令、花费超限），对应卡片需弹出**强干扰级的视觉警告**（如界面边缘发红、声音/视觉脉冲），并展示【批准】和【驳回】的明确操作。
4. **前端即控制面**
  * 对于 Runtime、Task、Plan 的高频操作，优先在前端提供直接操作入口；CLI 作为兜底，不应继续承担主操作路径。
  * 控制动作执行后必须保留最近活动记录，便于人工回溯。

---

## 5. 设计资产输出清单 (Design Deliverables Checklist)
UI团队在输出高保真图及切图阶段，请包含以下资产集：
* [ ] 全局颜色变量集 (Design Tokens - Dark Mode ONLY)
* [ ] 浅色优先 + 柔和深色模式的双主题变量集 (Google Palette)
* [ ] 拓扑连线画布组件集合 (节点块、连接点、连线、拖拽阴影)
* [ ] Schema 动态表单组件集合 (含嵌套对象的表单组、不同深度的缩进规范)
* [ ] Worker 状态指示灯及卡片集合
* [ ] 瀑布流树状追踪日志 (Trace/Span) 展开及折叠样式
* [ ] 多 Agent 并行任务的浮动进度条 (Plan Tracker UI)
* [ ] 控制台工作台资产：动作按钮、反馈 Toast、Activity Feed、任务快速创建表单