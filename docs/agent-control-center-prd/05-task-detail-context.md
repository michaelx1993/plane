# Task Detail 与 Task Context Directory

## Task Detail 目标

Task Detail 是单个 task 的执行控制台。它回答：

- 当前 task 的事实状态是什么？
- Agent 已经做了什么？
- workflow 走到哪一步？
- 当前需要谁做什么？
- 失败时人要补什么上下文，才能让 Agent 继续？
- 如果 task 仍在 To-do / Intake 节点，当前需求文档整理到什么程度？

## 页面结构

```text
Task Detail
  Header
    title / identifier / project / work directory
    active node
    owner: Agent / Human / System
    primary action

  Status
    rendered status.md
    edit status action

  Progress
    rendered progress.md
    append-only entries
    filters: all / agent / human / system

  Workflow Chain
    node timeline
    active node detail
    node actions

  Human Context
    comments
    add context / correction / feedback

  Artifacts
    Change Request
    commits
    checks
    release tags / images
    deployment URL / job
    run logs
```

## Header

Header 必须显示：

- task identifier 和 title
- active workflow node
- owner：哪个 Agent、哪个 Worker，或等待哪个 Human Gate
- state：running / waiting_for_human / failed / blocked / done
- primary action：
  - Human Gate：Approve / Return / Set auto
  - Blocked：Add context and return
  - Agent running：Open run detail
  - Done：View final summary

## Task Context Directory

每个 task 都应该有自己独立的 Task Context Directory。这个目录是 task 的上下文边界，用来承载人和 Agent 都能读取的任务文档。

Phase 1 的 source of truth 仍在 Plane DB，但产品模型和渲染结构按目录组织：

```text
tasks/<task-id>/
  prd.md
  status.md
  progress.md
```

Task Context Directory 和 Work Directory 是两个概念：

- Work Directory 是 Agent 执行代码的工作目录，包含一个或多个 repositories。
- Task Context Directory 是某个 task 的需求、状态、进度和人机交接文档目录。

二者逻辑分离。Agent 执行时同时读取：

```text
Task
  selected Work Directory
  task context directory
```

Phase 1 不要求 Task Context Directory 是 Work Directory 的真实子目录。未来可以将其镜像到 Work Directory 下：

```text
<work-directory>/.agent/tasks/<task-id>/
  prd.md
  status.md
  progress.md
```

该镜像只用于文件化查看、审计或本地协作，不是 Phase 1 source of truth。

最低文件集：

- `prd.md`：需求文档 / PRD，由 To-do / Intake 节点通过用户和 Intake Agent 对话整理出来。
- `status.md`：当前 task 的事实状态、workflow 位置、blocker、验证状态、release/deploy 状态和最终结论。
- `progress.md`：追加式进展日志，记录执行过程、决策、证据、Agent 结论和 handoff notes。

未来可以扩展：

```text
tasks/<task-id>/
  prd.md
  status.md
  progress.md
  artifacts.md
  decisions.md
  context/
  runs/
```

## prd.md / PRD

`prd.md` 是 task 的需求文档，也可以在 UI 上显示为 PRD。

来源：

- 用户新建 task 时的初始目标。
- To-do / Intake 节点中的多轮人机对话。
- Intake Agent 对背景、约束、验收标准、范围和 non-goals 的整理。

内容至少包括：

- 背景
- 目标
- 范围
- non-goals
- acceptance criteria
- work directory / repository context
- validation requirements
- 关键约束和风险

规则：

- Development 节点开始前，`prd.md` 必须达到可执行状态。
- 用户可以编辑。
- Intake Agent 可以建议修改或生成草案。
- Agent 后续执行必须读取该文档。
- Development 或后续节点需要修改 PRD 时，必须先把 task 退回 `To-do / Intake / PRD` 节点。
- 不允许在后续节点静默修改 PRD 并继续执行。
- 每次 PRD 修改都记录版本和 progress entry。

## status.md

每个 task 有自己的 `status.md`。

内容包括：

- 当前 task status
- PRD
- acceptance criteria
- workflow state
- blockers
- validation status
- release status
- deployment status
- final outcome

规则：

- 默认在 Task Detail 第一屏展示。
- 允许人工编辑。
- 记录 updated_by / updated_at / version。
- Agent 下次执行必须读取最新版本。

## progress.md

每个 task 有自己的 `progress.md`。

内容包括：

- append-oriented execution log
- detailed progress
- decisions
- evidence
- validation commands
- Agent conclusions
- handoff notes
- timestamps

规则：

- 默认展示在 status 后。
- 只追加，不直接改历史 entry。
- Agent、Human、System 都可以写入 progress entry。
- 每条 entry 关联 workflow node、run、time、author。

## Human Context

Human comments 用于补充信息，不替代 prd/status/progress。

失败后拖回节点前，应引导用户补充：

- failure diagnosis
- missing context
- correction instruction
- credential/environment note
- acceptance clarification

这些 comments 必须被 ACP/Agent 作为 task context 读取。

## Intake Conversation

当 task 处于 `To-do / Intake / PRD` 节点时，Human Context 区域承担需求澄清对话作用：

- 用户补充项目背景、目标、约束和验收标准。
- Intake Agent 基于对话更新 `prd.md`，并同步维护 `status.md` 的当前事实状态。
- `progress.md` 记录需求澄清过程和关键决策。
- Intake Agent 提示还缺什么信息。
- 默认需要用户点击“开始开发”确认后，task 才进入 Development。
- 如果当前 task 的 Intake 节点被设为 auto，Intake Agent 判断 PRD 已足够清楚后可以进入 Development。

## Artifacts

Artifacts 展示代码和发布事实：

- Change Request
- commits
- checks
- release version/tag/image/artifact/changelog
- deployment environment / URL / job
- smoke result
- rollback notes
- run logs

`Change Request` 是统一术语，可映射 GitHub Pull Request 或 GitLab Merge Request。

## 存储决策

Phase 1：

- Task Context Directory 的 source of truth 在 Plane DB。
- `prd.md` / `status.md` / `progress.md` 都由 Plane DB 存储并渲染。
- Markdown 是展示和 Agent-context 格式。
- `prd.md` 存当前需求版本。
- `status.md` 存当前版本。
- `progress.md` 由 append-only entries 渲染。
- ACP 通过 API/projection 读取后放入 prompt release。
- Project Meta Git 未来可镜像到：
  - `tasks/<task-id>/prd.md`
  - `tasks/<task-id>/status.md`
  - `tasks/<task-id>/progress.md`

Project Meta Git mirror 不是 Phase 1 source of truth。
