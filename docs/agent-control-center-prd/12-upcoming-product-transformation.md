# 后续产品改造总图

Status: Draft for execution
Last updated: 2026-06-27

本文件回答“CI 合入和后端底座逐步完成后，Plane fork 接下来应该怎么改，才能从项目管理工具变成 Agent 托管与流程控制中心”。

它不是替代 PRD，而是把现有 PRD、工程路线图和执行 backlog 收敛成下一阶段的产品改造顺序。

## 当前判断

Plane 的产品中心必须从传统 project board 转到 **task-centered agent operations**。

核心变化：

- 用户不是先看 ToDo / Backlog / Kanban，而是先看哪些 Agent 在跑、哪些 Human Gate 等我处理、哪些 task 被 block。
- Task Detail 不是 issue 表单，而是单 task 控制台，首屏展示 `status.md`、`progress.md`、`prd.md`、workflow chain、active node 和 run evidence。
- Agent、Prompt、Worker、Work Directory、Workflow Node、Human Gate 都是一等产品对象。
- Plane native state 只是 workflow active node 的派生兼容字段，不再作为主业务模型。

## 已有底座

已经具备或正在发布的底座：

- Agent / Prompt API。
- Worker / Work Directory / Repository API。
- Task Context Documents API。
- Workflow Instance / Human Gate API。
- 登录后进入 Agent Center / Tasks Center 的入口方向。
- Billing / Plan / Export 已从主入口移除。
- 中英文切换已上线。

这些底座仍偏 API 和页面壳，用户还不能顺畅完成“新建 Agent -> 绑定 Prompt -> 新建 Task -> 澄清 PRD -> 选择 Agent 执行 -> Review -> Release -> Deploy -> 看证据”的完整闭环。

## 下一阶段主目标

下一阶段不是继续补散点功能，而是打通三条端到端链路。

### 链路 1：Agent 与 Prompt 管理闭环

用户必须能在 Plane 上完成：

1. 新建 Prompt。
2. 创建 Prompt version，并设置 scope、kind、version policy。
3. 新建 Agent。
4. 给 Agent 勾选多个 Prompt，形成按顺序叠加的 prompt stack。
5. 设置 Agent 的默认 role、default worker、适用 workflow node。
6. 在 task 或 workflow node 上选择该 Agent。

验收标准：

- Agents 和 Prompts 不再是设置页隐藏能力，而是主导航下一等页面。
- 默认展示当前 workspace 可见的所有 Agent 和 Prompt。
- Prompt 可新增、编辑 metadata、创建新版本、archive。
- Agent detail 能看到 prompt stack、默认执行配置和最近 runs。
- 中英文文案完整。

### 链路 2：Task 控制台与 Workflow 操作闭环

用户必须能从 task 视角控制流程，而不是从 state board 视角管理任务。

用户路径：

1. 新建 task，默认进入 `To-do / Intake / PRD`。
2. 在 Intake 节点和 Agent 对话，沉淀 `prd.md`、`status.md`、`progress.md`。
3. 用户确认或 Intake auto 后进入 Development。
4. Agent 节点执行失败时进入 Blocked。
5. Human 可以补充 context，并把 task 拖回 Development / Review / Release / Deployment 等节点。
6. Human Gate 默认 manual，但当前 task 的节点可以切换为 auto。
7. Release 后仍经过 human gate，再进入 Deployment。

验收标准：

- Tasks Center 首屏优先显示 Waiting Human Gates、Blocked / Failed Agent Nodes、Running Agents、Active Tasks。
- Task Detail 第一屏按顺序展示 `status.md`、`progress.md`、`prd.md`。
- Workflow chain 能展示当前 active node、节点 owner、mode、assigned Agent、状态和可用动作。
- Human Gate 可 approve、return、set auto。
- Agent failed 会进入 Blocked，不会自动 skip 或继续。
- Plane native state 只跟随 active workflow node 派生同步。

### 链路 3：ACP / Worker / Evidence 回流闭环

Plane 应该是控制台和计分板，ACP / Worker 负责真实执行。

必须打通：

1. Plane 维护 Agent、Prompt、Worker、Work Directory、Task Context、Workflow 的 source of truth。
2. ACP 从 Plane 同步配置和 task run intent。
3. Worker 在真实机器上执行，复用宿主机环境。
4. ACP / Worker 把 run progress、conclusion、Change Request、commit、checks、release image、deployment result 回写 Plane。
5. Plane 在 Task Detail 中展示这些 evidence，并让下一次 Agent run 能读取最新 task context。

验收标准：

- Agent node detail 能看到 run progress 和结论。
- 用户能从 Task Detail 打开 Change Request、commit、check、release tag/image、deployment result。
- Release、Deployment、smoke test、rollback note 都能作为 evidence 写入 `progress.md` 或 artifacts。
- Prompt release 必须记录本次 run 使用的 prompt stack 和 task context snapshot，不能只引用 latest。

## 推荐改造顺序

```text
1. Agent / Prompt Library UI
2. Workers / Work Directories UI
3. Tasks Center + Task Detail shell 接真实 API
4. Workflow chain + Human Gate 操作 UI
5. Task Context editor：PRD/status/progress
6. ACP run evidence projection
7. Release / Deployment evidence 页面化
8. Auto mode 与异常 Blocked 体验打磨
```

排序理由：

- 后端 source tables 已经先行，下一步必须让用户可操作。
- Agent / Prompt 是“谁来做事、怎么做”的入口，必须先可配置。
- Work Directory 是“在哪些代码目录做事”的入口，真实开发任务离不开它。
- Task Detail 是所有执行状态、上下文和 evidence 的汇合点，应尽早接真实 API。
- ACP evidence 依赖 workflow、task context、worker resolution 和 run intent，适合在 UI 骨架稳定后接入。

## 第一批可开 PR

### PR 1：Agent / Prompt Library UI 可用化

范围：

- Agents 页面接真实 Agent API。
- Prompts 页面接真实 Prompt API。
- Agent create / edit。
- Prompt create / edit metadata / create version / archive。
- Agent prompt stack editor。
- 中英文文案。

不做：

- Prompt marketplace。
- 跨 workspace sharing。
- 复杂权限隔离。

### PR 2：Workers / Work Directories UI 可用化

范围：

- Workers 页面接真实 worker card API。
- Work Directories 页面接真实 work directory / repository / mount API。
- Project default work directory 配置入口。
- Task 创建或详情中的 work directory override。

不做：

- Plane 远程安装 worker。
- Plane 直接写宿主机文件系统。

### PR 3：Task Detail 接真实上下文与 workflow

范围：

- Task Detail 展示 `status.md`、`progress.md`、`prd.md`。
- Workflow chain 展示 workflow instance / nodes。
- Active node detail。
- Human Gate actions。
- Blocked node return flow。

不做：

- 完整 run logs viewer。
- 高级 workflow template builder。

### PR 4：Tasks Center 运行态首页

范围：

- Attention queue。
- Waiting Human Gates。
- Blocked / Failed Agent Nodes。
- Running Agents。
- Active Tasks。
- Recent Progress。

不做：

- 以 ToDo / Backlog / Kanban 作为默认首屏。
- 恢复 legacy project board 为主入口。

### PR 5：ACP Evidence projection

范围：

- Plane outbox / ACP projection 对齐。
- ACP run progress 回写。
- Change Request / commit / checks / release / deployment evidence 回写。
- Task Detail node evidence 展示。

不做：

- Plane 直接执行 worker。
- Plane 保存 secret value。

## 关键产品约束

- Task 是用户操作的中心，workflow node 是 task 当前执行位置。
- Project 仍存在，但主要用于归组、默认 Work Directory、默认 Agent、默认 workflow policy。
- 一个 task 默认使用 project work directory，但用户可以 override。
- Work Directory 可以绑定多个 repository。
- 每个 task 有独立 Task Context Directory：`prd.md`、`status.md`、`progress.md`。
- PRD 可以修改，但 Development 后修改 PRD 必须回到 Intake 节点。
- Progress 必须 append-only。
- Human Gate 默认 manual，但可按当前 task/node 改 auto。
- Agent node 失败进入 Blocked，等待人工补 context 后再拖回指定节点。
- Release 和 Deployment 是不同节点；release 产物是版本/image，deployment 产物是环境上线结果。

## 需要避免的歧路

- 不把 Plane 改回普通 kanban 项目管理工具。
- 不让 native state 成为业务主状态。
- 不把 Agent / Prompt 藏在设置页里。
- 不让 workflow 先做模板市场；Phase 1 只有默认软件交付 workflow。
- 不把 Work Directory 和 Task Context Directory 混成一个概念。
- 不只展示“运行中”，必须展示 evidence、结论、失败原因和下一步动作。
- 不把 secret value 存进 Plane 文档、日志或 run evidence；只保存 key、引用和可见性。

## 下一次设计讨论重点

优先只讨论三个问题：

1. **Task Detail 的首屏布局**：`status.md`、`progress.md`、`prd.md`、workflow chain 谁占主区域，谁放侧栏。
2. **Agent / Prompt Library 的编辑体验**：Prompt stack editor 是 drawer、detail page，还是 split view。
3. **Tasks Center 的 attention queue**：Waiting gates、blocked nodes、running agents 的排序和操作按钮如何设计。

这三个问题决定 UI 第一批 PR 的结构。其他如 workflow template builder、marketplace、细粒度权限、remote mirror 都放到 Phase 2。
