# 工程改造路线图

本文件把 PRD 转成可开发的工程 backlog。目标是渐进重构 Plane fork，让它从项目管理看板转为 Agent 托管与流程控制中心。

## 改造原则

- 不推倒 Plane，复用登录、workspace、project、work item、权限、API key、webhook 和部署体系。
- 新能力以 Agent Control Center 产品层增量接入，避免大爆炸式重写。
- 每个里程碑都要有可验收 UI、API 或数据证据。
- Plane DB 保存配置和 task context source of truth；ACP 保存 runtime projection 与执行状态。
- 所有代码变更走 worktree + PR，不直推 `preview`。

## Epic 0：实现护栏

目标：先建立测试和导航护栏，避免后续 UI 改造反复回归。

主要任务：

- 扩展 `apps/web/core/components/settings/agent-platform-settings.test.ts`，覆盖 Agent Control Center 主导航、路由、Task Context 三件套和 Work Directory-first 口径。
- 增加 API contract tests，覆盖 Work Directory、Task Context、Workflow Instance、Human Gate 的最小读写契约。
- 扩展 i18n 检查，至少覆盖 `en`、`zh-CN`、`zh-TW`。
- 文档同步检查：涉及 Agent Control Center 的行为变更必须更新 `docs/agent-control-center-prd/`。

验收：

- 本地 `pnpm --filter=web test` 通过。
- Agent config contract tests 通过。
- PR CI 的 Fork gate 和 Release smoke 通过。

## Epic 1：产品入口收敛

目标：首屏进入 Agent 托管与流程控制中心，不再默认进入 Kanban/state board。

主要任务：

- 新增主路由：
  - `/:workspaceSlug/tasks`
  - `/:workspaceSlug/agents`
  - `/:workspaceSlug/prompts`
  - `/:workspaceSlug/workers`
  - `/:workspaceSlug/work-directories`
- 登录后 workspace home 默认进入 Tasks Center。
- 主侧边栏新增 Tasks、Agents、Prompts、Workers、Work Directories。
- 弱化或隐藏 Projects、Views、Cycles、Modules、Backlog/ToDo 的首屏权重。
- 移除/隐藏 Billing/Plan 和 Export 用户入口。

主要代码区域：

- `apps/web/app/routes/core.ts`
- `apps/web/core/components/workspace/sidebar/`
- `packages/i18n/src/locales/*/navigation.json`
- workspace / project settings constants
- export / billing 相关菜单入口

验收：

- 用户登录后看到 Tasks Center。
- 主导航能直接进入 Agent、Prompt、Worker、Work Directory 管理。
- UI 中不出现 Billing/Plan 和 Export 主入口。

## Epic 2：数据模型与 API

目标：补齐 Agent Control Center 的 Plane-owned source tables 和 API。

新增或演进模型：

- `agent_work_directories`
- `agent_work_directory_repositories`
- `agent_worker_mounts`
- `agent_project_defaults`
- `agent_task_context_documents`
- `agent_task_progress_entries`
- `agent_task_workflow_instances`
- `agent_task_workflow_nodes`
- `agent_task_node_transitions`
- `agent_task_node_feedback`
- `agent_task_agent_assignments`

关键关系：

```text
Project -> default Work Directory
Task -> selected Work Directory override
Work Directory -> repositories
Work Directory + Worker -> local mount/path
Task -> Task Context Directory
Task -> Workflow Instance -> Workflow Nodes
Workflow Node -> assigned Agent override
```

API 方向：

- workspace-scoped CRUD for Agents、Prompts、Workers、Work Directories。
- task-scoped APIs for PRD/status/progress、workflow instance、node transition、human gate action。
- outbox event 覆盖新增/修改/删除，供 ACP projection 同步。

验收：

- 能创建 Work Directory，并登记多个 repositories。
- 能给 Project 设置默认 Work Directory。
- 能给 Task 覆盖 Work Directory。
- 能读写 `prd.md`、`status.md`、`progress.md`。
- workflow node 变化会派生更新 Plane native state。

## Epic 3：Agent Library / Prompt Library

目标：替换当前 settings 里的表单堆叠 UI。

主要任务：

- 建立 `Agents` 页面：Agent list、Agent detail、Prompt stack、default role、default worker、node bindings、recent runs。
- 建立 `Prompts` 页面：Prompt list、Prompt detail、version history、bindings、preview。
- Prompt 支持 create / edit metadata / create version / archive。
- Agent 支持 create / edit / prompt stack composition。
- 展示 Agent 适合哪些 workflow nodes。

验收：

- 用户能从主导航新建 Agent。
- 用户能从主导航新建、编辑、归档 Prompt。
- 用户能看到 Agent 绑定的 Prompt stack。

## Epic 4：Workers / Work Directories

目标：建立 Agent 托管的执行环境和代码目录管理面。

主要任务：

- Workers 页面展示 worker card、online/offline/draining/disabled、capabilities、heartbeat、recent runs。
- Work Directories 页面展示 root path、repositories、default worker、worker mount mapping、worktree policy。
- 支持一个 Work Directory 下注册多个 repositories。
- 支持同一 Work Directory 在不同 Worker 上配置不同 local path / mount。

验收：

- 用户能看到 Mac Studio / MBP worker。
- 用户能登记多仓 Work Directory。
- 新 Task 默认使用 Project Work Directory，也可覆盖。

## Epic 5：Tasks Center 与 Task 创建

目标：把首页改成运行态中心，并让新 task 进入 To-do / Intake / PRD。

主要任务：

- Tasks Center 展示 Top Metrics、Attention Queue、Active Task List、Recent Progress。
- 排序优先级：Waiting Human Gates、Failed/Blocked Agent Nodes、Stale Running Agents、Active Tasks、Recent Done。
- Task 创建页只保留 Agent 派发所需字段：
  - title
  - initial goal
  - project
  - Work Directory，默认项目目录，可覆盖
  - task default Agent，可选
  - initial context
  - Human Gate / Intake auto settings，可选
- 新建 task 后进入 To-do / Intake / PRD 节点。

验收：

- 新 task 能产生 workflow instance。
- 新 task 进入 Intake，而不是传统 Backlog/ToDo 看板列。
- Intake task 在首页显示为需求澄清中。

## Epic 6：Task Detail 与 Task Context Directory

目标：Task Detail 成为单任务控制台。

主要任务：

- Task Detail 首屏展示：
  - `prd.md`
  - `status.md`
  - `progress.md`
  - workflow chain
  - human comments
  - artifacts
- `prd.md` 在 To-do / Intake / PRD 节点中通过人机对话生成和修改。
- Development 后需要修改 PRD 时，必须退回 Intake。
- `status.md` 可编辑，记录版本。
- `progress.md` append-only，关联 node/run/author/time。
- Human comments 进入 Agent task context。

验收：

- 用户点开 task 先看到 PRD、status、progress。
- Agent 下次执行能读取三件套和人工 comments。
- PRD 修改会产生版本和 progress entry。

## Epic 7：Workflow Instance 与 Human Gate

目标：实现 Phase 1 默认 workflow 和人工门控制。

主要任务：

- 新 task 自动复制默认 Agent software delivery workflow。
- 支持 node-level assigned Agent override。
- Agent 选择优先级：

```text
node-level assigned Agent
-> task default Agent
-> project default Agent
-> system default general-purpose Agent
```

- Human Review / Human Gate 默认 manual。
- 当前 task 的 Human Gate 可设为 auto。
- Human Gate actions：
  - approve
  - return
  - set auto
  - block
- Agent node failed 后进入 Blocked / exception node。
- Blocked task 需人工补 context 后拖回指定节点。

验收：

- 用户能在 Task Detail 操作 Human Gate。
- Agent 失败不会自动 retry/skip/continue。
- workflow active node 派生同步到 Plane native state。

## Epic 8：ACP Run Evidence 集成

目标：把 ACP runtime 事实展示回 Plane。

主要任务：

- Agent node detail 展示 ACP run detail。
- 展示 prompt stack / prompt release。
- 展示 run progress、logs、conclusion。
- 展示 Change Request、commit、release、deployment evidence。
- ACP prompt release 读取：
  - `prd.md`
  - `status.md`
  - `progress.md`
  - human comments
  - selected Work Directory
  - resolved Worker mount/path
  - relevant repository metadata
  - available secret key names

验收：

- 用户知道 Agent 做了什么、结论是什么、产物在哪里。
- Plane 控制台、ACP run、worker progress 三者状态一致。

## 推荐 PR 切分

1. `docs/prd`：当前 PRD 与工程路线图。
2. `ui/navigation-entry`：主导航、登录默认页、隐藏 Billing/Export。
3. `api/work-directory`：Work Directory / repository / worker mount models and APIs。
4. `api/task-context`：PRD/status/progress documents and progress entries。
5. `ui/agent-prompt-library`：Agent / Prompt 主页面。
6. `ui/workers-directories`：Worker / Work Directory 页面。
7. `workflow-instance`：默认 workflow、node transitions、Human Gate。
8. `ui/tasks-center-detail`：Tasks Center 和 Task Detail。
9. `acp-run-evidence`：run detail、prompt release、progress/evidence 集成。

## 当前不做

- 多 workflow template picker。
- workflow template builder。
- marketplace / cross-workspace agent sharing。
- Billing / quota / cost accounting。
- repo-less task。
- 直接把 Task Context Directory 当真实文件 source of truth。
