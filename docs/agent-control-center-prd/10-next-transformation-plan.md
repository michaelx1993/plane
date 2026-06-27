# 下一阶段改造计划

Status: Draft execution plan
Last updated: 2026-06-26

本文件回答“入口收敛后，接下来具体改什么、按什么顺序改、每一步怎么验收”。

目标不是一次性重写 Plane，而是把 Plane fork 渐进改造成 Agent 托管与流程控制中心。每个 PR 都必须产生一个可验证的产品能力、API 契约或迁移护栏。

## 当前基线

已完成或正在合入：

- Agent Control Center 文档 PR 已合入。
- 主入口已新增 Tasks、Agents、Prompts、Workflows、Workers、Work Directories 页面壳。
- 登录后 workspace root 已进入 Tasks Center。
- Billing / Plan 和 Export 已从主要入口移除。
- 中文 / 英文切换已上线。
- 侧边栏从 legacy Projects chrome 收敛到 Agent Center 的修复在独立 PR 中处理。

当前仍是页面壳阶段。核心业务数据、Agent/Prompt CRUD、Task Workflow Instance、Human Gate、ACP evidence 还没有完整闭环。

## 改造主线

下一阶段按 4 条主线推进：

1. **数据底座**：Plane DB 持有 Agent、Prompt、Worker、Work Directory、Task Context、Workflow Instance 的 source of truth。
2. **控制台 UI**：Agents、Prompts、Workers、Work Directories、Tasks Center、Task Detail 从占位页变成可操作页面。
3. **执行编排**：新 task 自动进入默认 workflow，节点可以指定 Agent，Human Gate 可 manual / auto。
4. **运行证据回流**：ACP run、worker progress、Change Request、release、deployment evidence 回写并显示在 Plane。

## 推荐 PR 顺序

### PR 1：Agent / Prompt 数据模型与 API

目标：

- 建立 Agent Library 和 Prompt Library 的最小可写后端。
- 支持用户创建 Agent、创建 Prompt、创建 Prompt Version，并把多个 Prompt 绑定到 Agent。

范围：

- 新增 Agent、Prompt、Prompt Version、Prompt Binding 数据模型。
- Workspace-scoped API：
  - list / create / update / archive Agent
  - list / create / update / archive Prompt
  - create Prompt Version
  - bind / unbind Prompt to Agent
- Agent prompt stack 保存顺序、scope、kind、version policy。
- 保留历史 Prompt Version，不硬删被 run 使用过的版本。

验收：

- API 可以新建 Agent。
- API 可以新建 Prompt 并创建新版本。
- 一个 Agent 可以绑定多个 Prompt，并按顺序返回 prompt stack。
- 单元测试覆盖 create / update / archive / binding。

### PR 2：Agent Library / Prompt Library UI

目标：

- 把现在的页面壳变成可用的 Agent 和 Prompt 管理界面。

范围：

- Agents 页面：
  - Agent list
  - create / edit drawer or page
  - prompt stack editor
  - default role / default worker / workflow node bindings fields
- Prompts 页面：
  - Prompt list
  - create / edit metadata
  - create new version
  - archive
  - bindings preview
- 默认展示当前 workspace 可见的所有 Agent 和 Prompt。

验收：

- 用户能从主导航新建 Agent。
- 用户能从主导航新建、编辑、归档 Prompt。
- 用户能看到每个 Agent 绑定了哪些 Prompt。
- 中英文文案完整。

### PR 3：Worker / Work Directory / Repository 数据模型与 API

目标：

- 建立 Agent 执行环境和代码目录的配置底座。

范围：

- 新增 Worker card、Work Directory、Repository registry、Worker mount 数据模型。
- 支持一个 Work Directory 包含多个 repositories。
- Project 可以设置默认 Work Directory。
- Task 可以覆盖 Work Directory。
- Worker mount 支持同一 Work Directory 在不同 Worker 上解析到不同本地路径。

API contract：

- `agent-worker-cards`：登记 MBP、Mac Studio 等可见 worker card。
- `agent-work-directories`：登记逻辑 Work Directory、默认 worker、worktree strategy、PRD/status/progress 路径。
- `agent-work-directory-repositories`：把一个或多个 repository 绑定到 Work Directory，并保存相对路径、默认分支、worktree strategy。
- `agent-worker-mounts`：保存 Work Directory 在不同 worker 上的真实本地路径。
- `agent-project-defaults`：保存 Project 默认 Work Directory / Worker。
- Task Work Directory override endpoint：保存单个 task 的 Work Directory / Worker override。
- `agent-work-directory-resolution`：按 project、task、worker 解析最终 Work Directory、mount 和 repository context。

验收：

- API 可以登记 Mac Studio / MBP worker。
- API 可以登记一个多仓 Work Directory。
- Project 默认目录和 Task 覆盖目录都能读写。
- 单元测试覆盖多仓、mount、default/override 解析。

### PR 4：Workers / Work Directories UI

目标：

- 用户能在 Plane 上配置 Agent 能跑在哪里、能看到哪些代码目录。

范围：

- Workers 页面：
  - worker card
  - online / offline / draining / disabled
  - capabilities
  - heartbeat / recent runs 占位或真实 projection
- Work Directories 页面：
  - list / create / edit
  - repositories editor
  - worker mount editor
  - worktree policy / default branch / target branch override

验收：

- 用户能看到 MBP、Mac Studio 等 Worker。
- 用户能登记多仓 Work Directory。
- 新 task 可以默认继承 Project Work Directory，也可以覆盖。

### PR 5：Task Context Documents

目标：

- 每个 task 有自己的 `prd.md`、`status.md`、`progress.md`，并在 Task Detail 中展示。

范围：

- Plane DB 保存 task context source of truth。
- `prd.md` 当前版本可编辑，可版本化。
- `status.md` 当前版本可编辑，可版本化。
- `progress.md` append-only。
- Human comments / corrections 进入 Agent 可读 context。

验收：

- Task Detail 首屏展示 PRD、status、progress。
- 用户可以编辑 PRD/status。
- progress 只能追加，不能静默改历史 entry。
- Agent context API 能返回 PRD/status/progress/comments 的快照。

### PR 6：Workflow Instance 与 Human Gate

目标：

- 新 task 自动挂默认 Agent software delivery workflow。
- 用户从 task 视角控制流程，而不是从 Plane native state 视角管理任务。

范围：

- 新 task 创建 workflow instance。
- 默认节点：
  - To-do / Intake / PRD
  - Development
  - Code Review / Agent Review
  - Human Review
  - In Merge
  - Merged Gate
  - Release Version
  - Released Gate
  - Deployment
  - Deployed Gate
  - Done
- Node 支持 assigned Agent override。
- Human Gate 默认 manual，可在当前 task 上改 auto。
- Agent failed 后进入 Blocked / exception node。
- active workflow node 派生同步到 Plane native state。

验收：

- 新 task 默认进入 Intake。
- 用户能在 Task Detail approve / return / set auto。
- Agent node failed 不自动继续，会进入 Blocked。
- 用户补 context 后能拖回 Development、Review、Release 或 Deployment。

### PR 7：Tasks Center 与 Task Detail 操作闭环

目标：

- 首页真正成为 Agent 运行态中心。

范围：

- Tasks Center 展示：
  - Running Agents
  - Waiting Human Gates
  - Failed / Blocked Nodes
  - Active Tasks
  - Recent Progress
- Task Detail 展示：
  - workflow chain
  - active node detail
  - node actions
  - PRD / status / progress
  - human comments
  - artifacts
- 排序优先级：
  - Waiting Human Gates
  - Failed / Blocked Agent nodes
  - stale running nodes
  - normal active tasks
  - recently completed tasks

验收：

- 用户登录后能先看到需要自己处理的 gate 和 blocked task。
- 点进 task 能看到当前链路走到哪一步。
- 点 Agent node 能看到当前执行状态或最近结论。

### PR 8：ACP Run Evidence 集成

目标：

- Plane、ACP、Worker 三者状态打通。

范围：

- Plane outbox / ACP projection 同步 Agent、Prompt、Worker、Work Directory、Workflow、Task Context 变更。
- ACP run 回写：
  - prompt release
  - run progress
  - conclusion
  - logs
  - Change Request
  - commit / checks
  - release version / image
  - deployment result
- Task Detail 的 node detail 展示 run evidence。

验收：

- 用户能从 Agent node 看到 Agent 做了什么、结论是什么、产物在哪里。
- 下一次 Agent run 能读取最新 PRD/status/progress/human comments。
- Plane 控制台、ACP run、worker progress 三者状态一致。

## 第一批应该马上做的事

入口收敛完成后，优先做以下 3 件事：

1. **PR 1 Agent / Prompt API**：没有数据模型，UI 只能继续做假数据。
2. **PR 3 Worker / Work Directory API**：没有执行目录和 worker 解析，Agent 无法稳定开发多仓任务。
3. **PR 5 Task Context Documents**：没有 PRD/status/progress，Agent 缺少可持续读写的任务上下文。

推荐顺序：

```text
Agent / Prompt API
-> Worker / Work Directory API
-> Task Context Documents
-> Agent / Prompt UI
-> Workers / Work Directories UI
-> Workflow Instance
-> Tasks Center / Task Detail
-> ACP Run Evidence
```

原因：

- API 和 source tables 先落，后续 UI 才不会反复推倒。
- Work Directory 必须早于真实 Agent dispatch，否则多仓开发和 worker mount 会后补得很痛。
- Task Context Documents 必须早于 Workflow Instance，否则 Intake、Development、Review 没有统一上下文。

## 边界

下一阶段仍不做：

- workflow template builder。
- marketplace / cross-workspace sharing。
- billing / quota / cost accounting。
- repo-less task。
- 把 Task Context Directory 的真实文件镜像作为 source of truth。
- 直接让 Plane 管 worker lease、worker token 或 secret value。

## 风险与护栏

- **Plane native state 混淆**：所有新 UI 操作 workflow node，native state 只做派生兼容。
- **Prompt 历史不可追溯**：Prompt Version 一旦进入 run，不能硬删；run 必须记录 prompt release。
- **Work Directory 与 Task Context 混层**：Work Directory 是代码执行目录，Task Context Directory 是 task 文档边界。
- **ACP 同步漂移**：Plane 写配置时必须有 outbox；ACP projection 不能只靠临时接口拼状态。
- **UI 回归到项目管理视角**：新增页面和导航文案必须以 Agent 托管、Human Gate、Run Evidence 为中心。

## 每个 PR 的通用验收

- 中英文文案齐全。
- 单元测试覆盖新业务规则。
- API 变更有 contract tests。
- 涉及导航、入口、状态派生的变更必须补 regression test。
- 文档同步更新 `docs/agent-control-center-prd/`。
- 不恢复 Billing / Plan / Export 主入口。
