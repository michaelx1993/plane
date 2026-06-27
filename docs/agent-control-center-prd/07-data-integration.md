# 数据模型与 ACP 集成

## 分层

```text
Agent Control Center Product Layer
  Tasks Center
  Agent Library
  Prompt Library
  Workflow Instance
  Human Gate
  Worker / Work Directory / Repository Registry
  Run Evidence

Plane Compatibility Layer
  Work item container
  Workspace / project / member / permission
  Native state derived field
  Existing API / webhook / filters

ACP Runtime Layer
  Runtime projection
  Prompt release
  Worker dispatch / lease / heartbeat
  Run events / progress / completion
```

## Plane DB Source of Truth

Plane owns editable configuration and task context source data:

- User Agents
- Prompts
- Prompt Versions
- Prompt Bindings
- Workers cards
- Work Directories
- Repository registry items
- Project default Work Directory binding
- Task selected Work Directory override
- Worker mount/local path mapping for each Work Directory
- Project default Agent binding
- Task default Agent override
- Workflow node Agent override
- Task workflow instances
- Workflow nodes
- Node transitions
- Node feedback
- PRD document
- status document
- progress entries

ACP owns runtime state:

- runtime projection
- prompt release
- worker dispatch
- lease / heartbeat
- run events
- run progress
- completion

## Work Item 作为 Task 容器

复用 Plane work item 作为 task 容器。新增 Agent Control Center 相关表，不把所有逻辑塞进 issue description 或 comments。

## Native State 派生

Workflow active node 是主事实。Plane native state 由 active node 派生，用于：

- legacy API
- webhook
- filters
- old components
- ACP transition compatibility during migration

直接 mutation native state 的入口应隐藏、禁用，或路由到 workflow transition validation。

## Task Context 进入 Agent

Agent run context 必须读取：

- latest `prd.md`
- latest `status.md`
- rendered `progress.md`
- human comments / task feedback
- current workflow node
- work directory
- resolved Worker local path / mount for that work directory
- relevant repository metadata
- prompt stack
- available secret key names

这些内容进入 prompt release 或 task-context snapshot。

Work Directory 和 Task Context Directory 必须分开建模：

- Work Directory 提供代码执行上下文和 repository root。
- Task Context Directory 提供 `prd.md`、`status.md`、`progress.md` 等 task 文档。
- Phase 1 两者的 source of truth 都在 Plane DB / ACP projection，不依赖真实文件路径。
- 未来可以把 Task Context Directory 镜像到 `<work-directory>/.agent/tasks/<task-id>/`，但镜像不是主事实来源。

## Outbox / Projection

Agent、Prompt、Worker、Work Directory、Repository、Workflow、Task Context 的变更应写入 Plane outbox，由 ACP 轮询/同步 projection。

设计目标：

- Plane 是配置和用户入口。
- ACP 是执行控制面。
- Worker 是真实执行环境。
- 不让 Plane 直接管理 worker lease 或访问 worker secret value。
