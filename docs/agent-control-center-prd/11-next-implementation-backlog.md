# 下一阶段执行 Backlog

Status: Draft execution backlog
Last updated: 2026-06-26

本文件把 PRD 和工程路线图收敛成下一批可开发、可测试、可合入的 PR 队列。

Plane fork 的产品中心已经确定为 **Agent 托管与流程控制中心**。后续改造不能再以传统项目管理看板为中心，而要围绕 task、agent、prompt、worker、work directory、workflow、human gate 和 run evidence 组织。

## 当前基线

已完成：

- Agent Control Center PRD 已落到 `docs/agent-control-center-prd/`。
- 主入口已从 legacy project board 收敛到 Agent Center 方向。
- 登录后 workspace home 进入 Tasks Center。
- Billing / Plan 和 Export 已从主要入口移除。
- 中文 / 英文切换已上线。
- Agent / Prompt API 已合入并发布到 `plane-components-v0.0.23`。

进行中：

- Worker / Work Directory / Repository API 正在开发，用于支持多仓目录、worker mount、project default 和 task override。

尚未形成闭环：

- Agent Library / Prompt Library 仍不是主工作流下的一等可用 UI。
- Workers / Work Directories 仍缺少可配置 UI。
- Task Context Documents 还没有 Plane DB source of truth。
- Workflow Instance、Human Gate、Blocked/return/auto mode 还没有真实数据模型和 UI 操作闭环。
- ACP run evidence 还没有稳定回流到 Task Detail。

## 执行原则

- 每个 PR 只交付一个可验证能力，不做大爆炸式重写。
- 后端 source tables 和 contract tests 先落，UI 再接真实 API。
- Task 视角优先于 Plane native state 视角。
- Plane native state 只做 workflow active node 的派生兼容字段。
- Task Context Directory 和 Work Directory 分开建模。
- 所有应用层改动继续走 worktree + PR，不直推 `preview`。

## 第一批 PR 队列

### PR A：Worker / Work Directory API

状态：进行中。

目标：

- 建立 Agent 执行目录和 worker 解析底座。
- 支持多仓 work directory。
- 支持 Project 默认目录和 Task 级 override。
- 支持同一个 work directory 在不同 worker 上解析到不同 local path。

核心产物：

- `AgentWorkDirectory`
- `AgentWorkDirectoryRepository`
- `AgentWorkerMount`
- `AgentProjectDefault`
- `AgentTaskWorkDirectoryOverride`
- work directory resolution API
- Agent run intent payload 中带 resolved work directory context

验收：

- API 可登记 Mac Studio / MBP worker card。
- API 可登记一个包含多个 repositories 的 work directory。
- Project default 和 Task override 均可读写。
- resolution API 能返回 selected worker、mount、repositories、branch policy。
- contract tests 覆盖 multi-repo、mount、default/override resolution。

不做：

- Worker heartbeat / lease / claim。
- Plane 直接管理 worker token。
- repo-less task。

### PR B：Task Context Documents API

目标：

- 每个 task 拥有独立 `prd.md`、`status.md`、`progress.md` 的 Plane DB source of truth。
- 让 Agent 每次执行都能读取稳定 task context snapshot。

核心产物：

- Task PRD document current version。
- Task status document current version。
- Task progress append-only entries。
- Human comments / corrections 进入 Agent 可读 context。
- Task context snapshot API。

规则：

- `prd.md` 可编辑，但 Development 后修改 PRD 必须先回到 To-do / Intake / PRD 节点。
- `status.md` 可编辑并记录 version。
- `progress.md` 只能 append，不允许静默改历史 entry。
- 每次 PRD/status 变更要写 progress entry。

验收：

- API 可创建和读取 `prd.md`、`status.md`。
- API 可追加 `progress.md` entry。
- progress 历史不可通过普通 update 覆盖。
- snapshot API 返回 PRD/status/progress/comments/work directory/worker/repository context。

不做：

- 把真实文件系统镜像作为 source of truth。
- 自动同步到 `<work-directory>/.agent/tasks/<task-id>/`。

### PR C：Workflow Instance 与 Human Gate API

目标：

- 新 task 自动挂 Phase 1 默认 Agent software delivery workflow instance。
- Human Gate 默认 manual，但当前 task 上可改 auto。
- Agent node failed 后进入 Blocked / exception node，等待人工补 context 再拖回指定节点。

默认节点：

```text
To-do / Intake / PRD
-> Development
-> Code Review / Agent Review
-> Human Review
-> In Merge
-> Merged Gate
-> Release Version
-> Released Gate
-> Deployment
-> Deployed Gate
-> Done
```

核心产物：

- Task workflow instance。
- Workflow nodes。
- Node transitions。
- Human gate actions：approve、return、set auto、block。
- Agent assignment override：node-level -> task default -> project default -> system default。
- Active node 到 Plane native state 的派生同步。

验收：

- 新 task 默认进入 Intake。
- 用户可 approve / return / set auto。
- Agent failed 不自动 retry/skip/continue，而是进入 Blocked。
- 人工补充 context 后可拖回 Development、Review、Release 或 Deployment。

不做：

- Workflow template builder。
- 多模板选择器。
- 模板市场。

### PR D：Agent Library / Prompt Library UI

目标：

- 把 Agent 和 Prompt 从设置页里的隐藏表单变成主导航下的一等管理页面。

核心产物：

- Agents 页面：list、create、edit、prompt stack、default role、default worker、workflow node bindings。
- Prompts 页面：list、create、edit metadata、create version、archive、bindings preview。
- Agent detail 展示 prompt stack 顺序和 version policy。

验收：

- 用户能从主导航新建 Agent。
- 用户能从主导航新建、编辑、归档 Prompt。
- 用户能给 Agent 勾选多个 Prompt 作为初始化 prompt stack。
- 中英文文案齐全。

不做：

- Prompt marketplace。
- 跨 workspace prompt 共享。
- 权限细粒度隔离。

### PR E：Workers / Work Directories UI

目标：

- 用户能在 Plane 上配置 Agent 跑在哪里、能看到哪些代码目录。

核心产物：

- Workers 页面展示 worker card、status、capabilities、heartbeat/recent runs projection。
- Work Directories 页面支持 list/create/edit。
- repositories editor。
- worker mount editor。
- worktree policy / default branch / target branch override。
- Project default work directory 配置入口。
- Task 创建/编辑时可 override work directory。

验收：

- 用户能看到 MBP、Mac Studio 等 worker。
- 用户能登记多仓 Work Directory。
- 新 task 默认继承 Project Work Directory，也可覆盖。

不做：

- Plane 远程安装 worker。
- Plane 直接写宿主机文件系统。

### PR F：Tasks Center 与 Task Detail UI

目标：

- 首页成为 Agent 运行态中心。
- Task Detail 成为单任务控制台。

Tasks Center 必须优先展示：

- Waiting Human Gates。
- Failed / Blocked Agent Nodes。
- Running Agents。
- Active Tasks。
- Recent Progress。

Task Detail 首屏必须展示：

- `status.md`
- `progress.md`
- `prd.md`
- workflow chain
- active node detail
- human comments
- artifacts

验收：

- 用户登录后先看到需要自己处理的 gate 和 blocked task。
- 点进 task 能看到当前 workflow 走到哪一步。
- 点 Agent node 能看到当前执行状态或最近结论。
- Human Gate 可在详情页完成 approve / return / set auto。

不做：

- 以 ToDo / Backlog kanban 作为默认首屏。
- 让旧 state board 成为主控制面。

### PR G：ACP Run Evidence 集成

目标：

- Plane、ACP、Worker 三者状态打通，让用户能在 Plane 看到 Agent 做了什么、产物在哪里。

核心产物：

- Plane outbox / ACP projection 同步 Agent、Prompt、Worker、Work Directory、Workflow、Task Context。
- ACP run 回写 run progress、logs、conclusion。
- Change Request、commit、checks、release version/image、deployment result 展示到 Task Detail。
- Prompt release 记录 prompt stack 和 task context snapshot。

验收：

- Agent node detail 能看到 run detail。
- 用户能看到 Change Request / commit / release / deployment evidence。
- 下一次 Agent run 能读取最新 PRD/status/progress/human comments。
- Plane 控制台、ACP run、worker progress 三者状态一致。

不做：

- 让 Plane 直接执行 worker run。
- 让 Plane 保存 secret value。

## 推荐执行顺序

```text
Worker / Work Directory API
-> Task Context Documents API
-> Workflow Instance / Human Gate API
-> Agent / Prompt UI
-> Workers / Work Directories UI
-> Tasks Center / Task Detail UI
-> ACP Run Evidence
```

原因：

- Worker / Work Directory 是执行位置和代码上下文，不先落会阻塞真实 Agent 开发任务。
- Task Context 是 Agent 可持续工作的上下文，不先落会导致 workflow 只能做空壳流转。
- Workflow Instance 需要 Task Context 和 Work Directory 作为节点运行输入。
- UI 必须接真实 API，避免继续堆假数据和临时表单。
- ACP Evidence 最后打通，因为它依赖 workflow nodes、task context 和 worker resolution。

## 关键风险

- **产品中心漂移**：如果继续围绕 Kanban/state board 做 UI，会偏离 Agent 托管中心定位。
- **上下文混层**：Work Directory 是代码目录，Task Context Directory 是任务文档边界，不能合成一个字段。
- **Prompt 不可追溯**：run 必须记录 prompt release，不能只引用 latest prompt。
- **Human Gate 自动化失控**：auto mode 只能是当前 task 的 node-level 设置，不能默认改全局模板。
- **Worker 职责越界**：Plane 管配置和可见性，ACP/worker 管 lease、heartbeat、claim 和真实执行。

## 每个 PR 的通用验收门

- contract tests 覆盖新增 API。
- UI 改动覆盖中英文文案。
- workflow/native state 相关改动必须有 regression tests。
- 文档同步更新 `docs/agent-control-center-prd/`。
- 不恢复 Billing / Plan / Export 主入口。
- 不把 secret value 写入 Plane 文档或日志。
