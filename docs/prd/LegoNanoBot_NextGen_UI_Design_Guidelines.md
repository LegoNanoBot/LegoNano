# LegoNanoBot - 下一代 UI/UX 设计指导说明原则 (UI/UX Design Guidelines)

## 1. 概述与设计愿景 (Overview & Vision)
LegoNanoBot 正在向一个**乐高式的插件化多智能体操作平台**演进。系统不仅提供零门槛的新手接入体验，同时为极客和开发者提供极其深度的系统“透视”与“编排”能力。
**设计主旨**：把复杂的 Multi-Agent 架构和冗长的执行日志，转化为直观、可控、如拼装乐高般愉悦的交互体验。

**对标竞品/灵感来源**：
* 布局与极简感：**Vercel**、**Linear**
* 节点拓扑与画布交互：**Langflow**、**ComfyUI**
* 开发者日志诊断：**Chrome DevTools (Network 视图)**、**DataDog**

---

## 2. 设计语言与系统基调 (Design Language)

### 2.1 风格定调：Dark Mode First (深色模式优先)
* **目标受众**：面向极客、开发者及 AI 训练师，系统必须**默认且全局强制深色模式 (Dark Theme)**。
* **视觉感受**：冷峻、现代、专业。避免过多的大面积鲜艳色块，通过高对比度文字和局部发光特效体现“科技感”。
* **语义色彩**：
  * **🟢 运行正常 (Healthy)**: 翠绿色 / 荧光绿 (用于 Worker 在线、心跳正常)
  * **🟡 等待/挂起 (Pending)**: 琥珀色 / 荧光橙 (用于模型思考中、等待 Human-in-the-loop 介入)
  * **🔴 异常/报错 (Error)**: 珊瑚红 / 警示红 (用于工具调用失败、Token超限断路)
  * **🔵 知识/技能 (Skills)**: 科技蓝 / 赛博蓝 (用于区分拓展技能和核心组件)

### 2.2 字体与排版 (Typography)
* **系统字体**：无衬线现代字体 (如 Inter, Roboto, Helvetica Neue)。
* **等宽字体 (Monospace)**：用于所有的代码块、日志、X-Ray Trace ID 和 JSON Schema 输出 (推荐：JetBrains Mono, Fira Code)。
* **信息层级**：通过字重(Weight)和灰度明暗(Opacity)而非字号差异来构建复杂的参数表单层级。

---

## 3. 核心视图布局设计建议 (Core View Layouts)

### 3.1 零门槛部署引导页 (Zero-Barrier Setup Wizard)
* **场景**：用户首次安装或初始化一个全新 Bot。
* **设计原则**：**极其克制、单线程操作**。全屏聚焦(Focus Mode)，移除侧边栏。引导采用分步式 (Step 1: API Key -> Step 2: 选择 Channel -> Step 3: 赋予 Persona)。
* **要求**：微动效加持（如对接成功时的“点亮”连线动画），让硬核的配置过程具有“开箱即用”的游戏感。

### 3.2 全局仪表盘与终端群集 (Dashboard & Worker Fleet)
* **场景**：统览当前主机上运行的所有 Bot Worker 状态。
* **视图建议**：
  * **数据矩阵/卡片流**：每一个运行的 Bot 是一个抽象卡片。卡片内必须包含：头像/名字、🟢状态灯、当前正在使用的 Provider (如 OpenAI/DeepSeek)、以及一个**微型火花线趋势图 (Sparkline)** 展现该 Bot 最近的吞吐活跃度。
  * **控制区**：悬浮显示一键 Start / Stop / Restart 操作按钮。

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

---

## 4. 关键交互原则 (Interaction Principles)

1. **高频数据的性能降级与虚拟化**
   * X-Ray 日志可能在 1 秒内推入百条数据。设计组件时默认需支持**虚拟列表 (Virtual Scrolling)**，杜绝页面抖动卡顿。
   * 新消息/日志到底部时，应自带“钉住 (Pin to bottom)”按钮。
2. **Schema-Driven 统一表单视觉**
   * 必须基于 JSON Schema 设计一套覆盖全部输入形态的“表单组件库”（如：String、Number、Enum、Array of Objects）。因为这些配置项都是按插件动态生成的。
3. **上帝之手 (Human-in-the-loop)**
   * 当安全引擎触发（如面临危险命令、花费超限），对应卡片需弹出**强干扰级的视觉警告**（如界面边缘发红、声音/视觉脉冲），并展示【批准】和【驳回】的明确操作。

---

## 5. 设计资产输出清单 (Design Deliverables Checklist)
UI团队在输出高保真图及切图阶段，请包含以下资产集：
* [ ] 全局颜色变量集 (Design Tokens - Dark Mode ONLY)
* [ ] 拓扑连线画布组件集合 (节点块、连接点、连线、拖拽阴影)
* [ ] Schema 动态表单组件集合 (含嵌套对象的表单组、不同深度的缩进规范)
* [ ] Worker 状态指示灯及卡片集合
* [ ] 瀑布流树状追踪日志 (Trace/Span) 展开及折叠样式
* [ ] 多 Agent 并行任务的浮动进度条 (Plan Tracker UI)