# LegoNanoBot - 前端跨组件系统与设计规范文档 (Design System & Components)

## 1. 概述 (Overview)

本文档基于 `LegoNanoBot_NextGen_PRD.md` 与参考竞品 OpenAkita 的架构，构建 LegoNanoBot 全新一代可视化控制面板的底层设计系统。系统严格遵循 **Dark Mode First（深色模式优先）**，定调整体视觉为冷峻、现代、专业的极客风格。

---

## 2. 设计令牌 (Design Tokens)

我们将提取以“科技蓝”为主品牌色的 Token 系统，所有面板交互均基于此设计体系。

### 2.1 颜色系统 (Color System)

深色模式下，色阶针对暗色背景重新映射高对比度。

#### 品牌主色 (Primary: Cyber Blue)
用于“知识/技能(Skills)”、可拖拽核心组件、主按钮和激活状态。

* `primary-50` : `#E6FAFF`
* `primary-100`: `#CCF6FF`
* `primary-200`: `#99EDFF`
* `primary-300`: `#66E3FF`
* `primary-400`: `#33DAFF`
* **`primary-500`: `#00D1FF` (Base Brand Color)**
* `primary-600`: `#00A7CC` (Hover states)
* `primary-700`: `#007D99` (Active states)
* `primary-800`: `#005466`
* `primary-900`: `#002A33`

#### 语义系统颜色 (Semantic Colors)

**正常/运转 (Healthy - Emerald Green)** -> 用于 Worker 在线、心跳正常
* `success-400`: `#34D399`
* **`success-500`: `#10B981`**
* `success-600`: `#059669`

**挂起/等待 (Pending - Amber)** -> 用于模型思考中、等待 Human-in-the-loop 介入
* `warning-400`: `#FBBF24`
* **`warning-500`: `#F59E0B`**
* `warning-600`: `#D97706`

**异常/断路 (Error - Coral Red)** -> 用于工具调用失败、Token超限
* `danger-400`: `#FB7185`
* **`danger-500`: `#F43F5E`**
* `danger-600`: `#E11D48`

#### 背景与中性色 (Surface & Neutral: Dark Theme)
极简的暗色灰阶。

* `surface-bg`: `#0F111A` (最底层的画布/背景)
* `surface-panel`: `#1A1D27` (浮浮窗、卡片、侧边栏)
* `surface-elevated`: `#24283B` (第二层级的悬浮模块如 X-Ray Logs)
* `neutral-100`: `#F1F5F9` (Primary Text)
* `neutral-300`: `#CBD5E1` (Secondary Text)
* `neutral-500`: `#64748B` (Muted / Placeholder / Borders)
* `neutral-800`: `#1E293B` (Dividers)

### 2.2 字体排版系统 (Typography System)

遵循现代几何黑体结合等宽字体设计，建立 `1.25` Ratio (Major Third) 层级。

* **Font Sans (系统主字体)**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`
* **Font Mono (代码与日志字体)**: `JetBrains Mono`, `Fira Code`, `monospace` (用于 X-Ray Trace ID, Logs, JSON Schema)

**字体缩放 (Font Scale)**
* `text-xs`: 12px (Line height 16px) - 用于辅助信息 / Badge
* `text-sm`: 14px (Line height 20px) - 用于日志树状图节点/次要描述
* `text-base`: 16px (Line height 24px) - 全局基准、表单输入框
* `text-lg`: 20px (Line height 28px) - 卡片/模块标题
* `text-xl`: 25px (Line height 32px) - 弹窗标题
* `text-2xl`: 31px (Line height 40px) - Dashboard Big Stats

### 2.3 间距与布局层级 (Spacing & Layout)

基于 **8pt Grid**，支持高效率排版。

* `space-1`: 4px - 图标与文字间隙
* `space-2`: 8px - 紧凑组件内部间距 (Button, Input padding-block)
* `space-3`: 12px - 默认内边距
* `space-4`: 16px - 卡片内部标准 Padding
* `space-6`: 24px - 模块间距 (Dashboard Panels)
* `space-8`: 32px - 页面版块分隔
* `space-12`: 48px - 大区域/列分隔

### 2.4 边框与阴影与特效 (Borders, Shadows & FX)

* **边框圆角 (Radius)**: 
  * `radius-sm`: 4px (Buttons, Inputs)
  * `radius-md`: 8px (Cards, Modals)
  * `radius-lg`: 12px (Main Layout Wrappers)
* **深色模式质感发光 (Neon Glow)**: 代替传统阴影，关键行为节点应采用彩色弥散阴影 `0 0 12px rgba({color}, 0.3)`。

---

## 3. 核心组件架构体系 (Component Architecture)

响应 PRD 中“Schema-Driven”与“无代码拓扑”的要求，划定前端组件层级。

### 3.1 基础原子组件 (Atoms)

1. **CyberButton (`<CyberButton>`)**:
   * 变体：`primary`, `secondary`, `danger`, `ghost`
   * 特性：悬停有微光动效 (Neon hover FX)，禁用态采用 `opacity-50` 且置灰。
2. **StatusNodeIndicator (`<StatusIndicator>`)**:
   * 必须严格对应 `Healthy`, `Pending`, `Error` 的呼吸闪烁动效 (Pulse Animation)。
3. **DataLabel (`<DataLabel>`)**:
   * 用来容纳 Trace ID, Hash 或 Token 统计的小标签，必须强制应用 `JetBrains Mono`。

### 3.2 表单微单元与反射组件 (Molecules: Schema Elements)

核心面板需大量通过 JSONSchema 反射配置。所以定义如下标准表单模块：
1. **SchemaStringInput / SchemaSecretInput**: `Provider` 密钥输入（如 OpenAI key），自带一键显示/隐藏，输入框处于 `:focus` 状态时，边缘产生一层 2px 的 `primary-500` 发光边框。
2. **SchemaDropdown / MultiSelect**: 支持模糊搜索的深色下拉，用于选择可用的 `LLM Models` 列表或 `Memory` 类型。
3. **ArrayObjectBlock (`<SchemaArrayEditor>`)**:
   针对复杂的如拦截器规则数组（Rules list），须支持拖拽排序与折叠/展开，保持深层次缩进树状清晰，左侧加入引导辅助线 (Guide lines)。

### 3.3 有机复杂体与视图 (Organisms)

1. **Lego Node 画布节点 (`<PluginNodeCard>`)**
   * 用于 "乐高工程车间"。包含 `Header`（展示组件Logo与类别标志）、`Port I/O` (左右连接锚点，悬停有磁吸吸附光标动效)、以及 `Body` (收起的关键状态)。
2. **Worker 矩阵仪表卡 (`<WorkerFleetCard>`)**
   * 组件拆解：上层为 Worker Nama + StatusIndicator，中层为微型热力图 (Sparkline chart) 展示资源占用，下层为浮动的启停/重启操作按钮栏 (Action Bar)。
3. **瀑布流追踪树 / X-Ray 视图 (`<XRayWaterfallTree>`)**
   * X-Ray 沙盒右侧的核心模块。必须具有高度折叠性和懒加载 (Virtual Scrolling)。
   * 层级渲染：采用缩进与左侧辅助线，每一层带有一个耗时小标签（如 `34ms` `(Model Thinking)`）。

---

## 4. 响应式与性能降级 (Responsive & Performance)

### 4.1 终端适配策略
由于强依赖可视化与拖拽：
* **Desktop (`xl: > 1024px`)**：完全体（双侧栏 + 画布 + 动态侧边栏展开），最高的信息密度。
* **Tablet (`md: 640px - 1024px`)**：自动收起左侧插件列表、X-Ray 悬浮化处理为侧边划出抽屉 (Drawer) 以保证主操作区空间。
* **Mobile (`xs: < 640px`)**：不支持全量蓝图编辑，降级为卡片矩阵操作（Worker fleet 只读模式与极简表单）。

### 4.2 数据层与视图优化
* 针对 X-Ray 视图与 Worker Ticker 实时日志推流，在接收高频 WebSocket 消息（>50 msg/s）时，要求前端组件开启 `requestAnimationFrame` 防抖和组件池的 Virtual List，以保证滚动不丢帧。

---

## 5. 开发者交接与落地准备 (Developer Handoff)

### 5.1 CSS 变量生成挂载示例
在 React/Vue 顶层 `App.css` (或 Tailwind / UnoCSS 配置) 中引入以下令牌系统（节选）：

```css
:root {
  /* Surface & Background */
  --surface-bg: #0F111A;
  --surface-panel: #1A1D27;
  
  /* Primary Cyber Blue */
  --color-primary-400: #33DAFF;
  --color-primary-500: #00D1FF;
  --color-primary-600: #00A7CC;
  
  /* Semantic */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #F43F5E;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* UI FX */
  --shadow-neon-primary: 0 0 12px rgba(0, 209, 255, 0.3);
  --shadow-neon-danger: 0 0 12px rgba(244, 63, 94, 0.3);
}

body {
  background-color: var(--surface-bg);
  color: var(--neutral-100);
  font-family: var(--font-sans);
}
```

### 5.2 Next Steps（下一步开发指引）
1. [ ] **构建前端脚手架**：采用 Vite + React/Vue 3 + Typescript。
2. [ ] **配置 Tailwind CSS**：根据 `#2. 设计令牌` 的颜色和间距设定，自定义化扩展 `tailwind.config.js` 的 `theme` 字段。
3. [ ] **引入核心依赖库**：
   * 可视化蓝图节点库：考虑引入 `React Flow` / `Vue Flow` 作为 "乐高工程车间" 基础。
   * 日志虚拟加载：引入 `react-window` / `vue-virtual-scroller` 支持高频日志。
   * 表单反射：引入类似 `react-jsonschema-form` 予以改造适配设计规范样式。