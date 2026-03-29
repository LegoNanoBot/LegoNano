# LegoNanoBot - NextGen Frontend Sub-PRD

## 1. Problem Statement
The current LegoNanoBot relies heavily on CLI and configuration files for operation, resulting in a high barrier to entry for end users and inadequate visualization for complex Multi-Agent operations. Benchmarking against industry-leading open-source platforms like OpenAkita, LegoNanoBot lacks a comprehensive GUI config (Zero-Barrier Setup), real-time visibility into AI reasoning (Chain-of-Thought), and intuitive task management capabilities. The goal of this frontend PRD is to transform LegoNanoBot into a seamless, visual, and highly interactive control panel that accommodates both initial onboarding and deep, multi-agent observability.

## 2. Success Metrics
* **Zero-Barrier Conversion Rate**: 90% of new users can complete initial configuration and create a bot within 5 minutes entirely via the UI without touching the CLI.
* **Observability Effectiveness**: Developers can trace 100% of Agent interactions (Memory, Provider, Channel) via the real-time X-Ray Sandbox.
* **Component Reusability**: Frontend architecture (Vue 3 / React) maintains high modularity, allowing rapid addition of new tool/plugin configuration forms via dynamically rendered JSONSchemas.

## 3. Scope
### In-Scope
* **Zero-Barrier Setup Wizard**: Step-by-step onboarding flow for API keys, channels, and persona profiles.
* **Global Dashboard & Worker Fleet**: Real-time monitoring matrix for CPU/Memory, heartbeat, and active task states per Worker.
* **Node-Based Topology Designer**: "Lego-style" drag-and-drop workspace for assembling bots from Channel, Provider, and Memory plugins.
* **X-Ray Sandbox (Observability)**: WebSocket-driven interface displaying tree/waterfall views of traces, Deep Thinking (chain-of-thought) streams, and API payload payloads.
* **Skill Marketplace UI**: Interface for browsing, viewing, and one-click installing skills/plugins.
* **Plan Mode & Task Progress**: Visualizing task decomposition, step-by-step progress bars, and Human-in-the-loop intervention prompts.

### Out-of-Scope
* Server-side routing logic and database query implementation (handled by Backend PRD).
* Mobile-native App development (initially focusing on responsive Web for this phase).

## 4. Key Features & Gap Analysis (vs. OpenAkita)

Based on the benchmark of OpenAkita's *Full Feature List*, the following capabilities must be integrated into the LegoNanoBot NextGen Frontend:

| Feature Name | Description | Priority | Gap Status vs OpenAkita |
|--------------|-------------|----------|-------------------------|
| **Zero-Barrier Setup UI** | Complete GUI config and onboarding wizard to replace manual YAML editing. | P0 | 🚨 Missing in LegoNanoBot |
| **Lego Plugin Studio** | Visual drag-and-drop assembly of Bot architectures (Providers, Channels, Memory). | P0 | ✅ Planned in Core PRD |
| **X-Ray Sandbox** | Dual-pane simulated chat + trace waterfall (similar to Chrome Network tab). | P0 | ✅ Planned in Core PRD |
| **Deep Thinking UI** | Real-time steaming visualization of the agent's chain-of-thought and intermediate ReAct steps. | P1 | 🚨 Missing in LegoNanoBot |
| **Plan Mode Tracking** | Auto task decomposition tree with real-time step tracking and floating progress bars. | P1 | 🚨 Missing in LegoNanoBot |
| **Skill Marketplace** | Interface supporting open search and one-click installation of community skills. | P2 | 🚨 Missing in LegoNanoBot |
| **Multi-Agent Dashboard** | Visualizing parallel delegation, handoffs, and failovers among multiple specialized agents. | P1 | 🔄 Partial in Core PRD |

## 5. User Experience & Design Guidelines (UX/UI)
* **Theme**: Modern, minimalist, developer-focused, mandatory default **Dark Mode**.
* **Dynamic Forms**: Frontend must render settings forms on the fly based on JSONSchemas provided by backend plugins (eliminating hardcoded configuration forms).
* **Responsive State**: Worker Matrix and log streams must function without stutter under high update frequencies (employing virtualization for the X-Ray logs).

## 6. Implementation Roadmap
* **Milestone 1**: Project scoping, tech stack setup (React/Vue 3 + Vite), Global Dashboard skeleton, and Dynamic Plugin Configuration Forms.
* **Milestone 2**: WebSocket integration, establishing the X-Ray Sandbox and Deep Thinking streaming text views.
* **Milestone 3**: Zero-Barrier Setup Wizard, Plan Mode progress tracker, and Skill Marketplace frontends.