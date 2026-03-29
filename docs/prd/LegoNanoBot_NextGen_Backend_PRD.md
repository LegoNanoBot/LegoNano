# LegoNanoBot - NextGen Backend Sub-PRD

## 1. Problem Statement
LegoNanoBot’s existing backend needs to evolve from a basic polling-based script into a high-concurrency, Cloud-Native Supervisor platform capable of orchestrating multi-agent collaboration. By comparing our trajectory with OpenAkita's robust capabilities, there are substantial architecture gaps—especially regarding deep memory management, runtime supervision/reasoning loops, and proactive self-evolution mechanisms. This PRD details the roadmap for backend upgrades to achieve competitive feature parity and cloud scalability.

## 2. Success Metrics
* **Plugin Architecture Integrity**: 100% of functional components (Channels, Providers, Memories, Skills) decoupled into dynamically loadable plugins.
* **Supervisor Throughput**: Can concurrently persist and route heartbeats, X-Ray logs, and workloads for 50+ Agent Workers without bottlenecks.
* **Intelligent Autonomy**: Agents achieve a highly successful task completion rate via Plan Mode (Task Decomposition) and ReAct reasoning, with automated fallback logic for error recovery.

## 3. Scope
### In-Scope
* **Supervisor Gateway (Control Plane)**: REST/GraphQL API for Frontend, unified Multi-Agent routing, Worker lifecycle management, and WebSocket streams for X-Ray logs.
* **Dynamic Plugin System**: Hot-reloadable plugins governed by YAML manifests and JSONSchema reflection.
* **Plan Mode & ReAct Engine**: Complex workflow delegation, automatic task decomposition, and an explicit 3-phase reasoning loop with checkpoint/rollback.
* **3-Layer Memory Architecture**: Upgrading from simple SQLite to a localized Core + Working + Dynamic retrieval context framework. This component will be implemented via the **Plugin Architecture (Memory Plugin)** to ensure high modularity and support flexible storage backends.
* **Proactive Engine**: Cron-like triggers and contextual awareness algorithms triggering spontaneous greetings, follow-ups, and self-checks.
* **Self-Evolution & Runtime Safety**: Implemented by tightly coupling **Skills** with the **XRAY** observability bus. XRAY traces feed deep context into internal reflection skills for self-evolution and auto-repair. Meanwhile, specialized supervisor skills read real-time XRAY logs to enforce resource budgets, detect tool thrashing, and apply strict access policies (POLICIES.yaml).

### Out-of-Scope
* Specific Frontend component renderings.
* Replacing underlying upstream LLM API limits (restricted by physical bounds).

## 4. Key Features & Gap Analysis (vs. OpenAkita)

Based on the benchmark of OpenAkita's *Full Feature List*, the following capabilities must be integrated into the LegoNanoBot NextGen Backend:

| Feature Name | Description | Priority | Gap Status vs OpenAkita |
|--------------|-------------|----------|-------------------------|
| **Multi-Agent Supervisor** | Router supporting parallel delegation, automatic handoff, failover, and process heartbeats. | P0 | ✅ Planned in Core PRD |
| **ReAct Reasoning Loop** | Explicit 3-phase reasoning, rollback checkpoints, and loop/thrashing detection. | P0 | 🚨 Missing in LegoNanoBot |
| **Plan Mode Engine** | Engine converting complex prompts to DAG auto task decomposition for progressive execution. | P1 | 🚨 Missing in LegoNanoBot |
| **3-Layer Memory** | Integration of Working + Core + Dynamic retrieval memory tiers and AI-driven compaction (Via Memory Plugins). | P1 | 🚨 Missing in LegoNanoBot |
| **Proactive Engine** | Agents taking initiative: greetings, task follow-ups, idle chat, adapting frequency locally. | P2 | 🚨 Missing in LegoNanoBot |
| **Self-Evolution & Check** | Daily automated self-check loops, repair mechanisms, and auto-generation of on-the-fly skills (Combined with XRAY & Skills). | P2 | 🚨 Missing in LegoNanoBot |
| **Runtime Safety Controls** | Budget limiting (Tokens/Cost), deterministic validators, and dangerous-op confirmation gates (Enforced via XRAY & Skills). | P1 | 🚨 Missing in LegoNanoBot |
| **Cloud-Native Memory** | Distributed, high-concurrency Cloud Memory plugins (e.g., PostgreSQL/Redis/Vector DB). | P1 | 🔄 Partial in Core PRD |

## 5. Architectural Design Principles
* **Stateless Default**: The core routing and execution engines should remain as stateless as possible, delegating conversational continuity and caching out to external Memory extensions (supporting Serverless/Lambda deployments).
* **Strict Factory Patter**: No hardcoded references to specific large models or channels in `nanobot/core`. Everything is injected at runtime.
* **Observability First**: Before emitting any prompt to the LLM or saving to memory, telemetry span logs must be pushed via an event bus to the Supervisor for debugging/X-Ray.
* **Fail-Safe & Fallback**: Network failures or tool execution crashes must be gracefully captured, and the ReAct reasoning loops must contain maximum depth thresholds to prevent infinite recursive LLM calls (Tool thrashing detection).

## 6. Implementation Roadmap
* **Milestone 1**: Solidify the fundamental Dynamic Plugin loading mechanism, configuration schemas, and Supervisor gateway (Heartbeats and APIs).
* **Milestone 2**: Establish the fundamental X-Ray event bus (WebSocket broadcast) and implement ReAct Reasoning loop safeguards (timeout & thrashing control).
* **Milestone 3**: Develop backend models for 3-Layer Memory, the Plan Mode decomposition engine, and Runtime Safety frameworks.
* **Milestone 4**: Extend capability to the cloud (PostgreSQL standard plugins) and build the Proactive Engine scheduler for worker routines.