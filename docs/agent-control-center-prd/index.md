# Agent 托管与流程控制中心 PRD

Status: Draft PRD
Last updated: 2026-06-26
Source repo: `michaelx1993/plane`

## 定位

Plane fork 的目标不是继续做通用项目管理看板，而是成为 **Agent 托管与流程控制中心**。

Plane work item 只是 task 的承载容器；真正的一等产品对象是：

- Agent
- Prompt
- Worker
- Work Directory
- Workflow Instance
- Run
- Human Gate
- Evidence

## 章节索引

1. [产品定位](./01-product-positioning.md)
2. [信息架构与首页](./02-information-architecture.md)
3. [Agent Library 与 Prompt Library](./03-agent-prompt-library.md)
4. [默认 Workflow 与节点规则](./04-task-workflow.md)
5. [Task Detail 与 Task Context Directory](./05-task-detail-context.md)
6. [Workers、Work Directories 与 Repositories](./06-workers-work-directories.md)
7. [数据模型与 ACP 集成](./07-data-integration.md)
8. [Phase 1 实施分期](./08-implementation-plan.md)
9. [工程改造路线图](./09-engineering-transformation-plan.md)
10. [下一阶段改造计划](./10-next-transformation-plan.md)

## Phase 1 总原则

- 第一阶段只提供一个默认 workflow：Agent software delivery workflow。
- 不做 workflow template picker，不做模板市场。
- Human Gate 默认 manual，但当前 task 上可以改成 auto。
- Agent 节点失败后进入 Blocked/异常节点，等待人工补充上下文后再拖回某个节点。
- `prd.md` / `status.md` / `progress.md` 的 source of truth 在 Plane DB。
- Plane native state 只是兼容字段，由 workflow active node 派生。
- 软件交付类 task 绑定 Work Directory，而不是只绑定单个 repository。
- Billing/Plan 和 Export 从主 UI 移除。
