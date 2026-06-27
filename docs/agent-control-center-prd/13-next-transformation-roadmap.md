# 下一阶段改造执行路线图

Status: Draft for execution
Last updated: 2026-06-27
Baseline: `plane-components-v0.0.27`

本文件把 PRD、后端底座、当前 UI PR 和后续开发顺序收敛成一份可执行路线图。目标不是继续补 Plane 的传统项目管理能力，而是把它重构成 **Agent 托管与流程控制中心**。

## 当前基线

已完成并部署到 MBP 的基线：

- `0.0.27` 已包含 Agent / Prompt API、Worker / Work Directory API、Task Context Documents API、Workflow Instance / Human Gate API。
- Plane native state 已被定位为 workflow active node 的派生兼容字段，不是业务主状态。
- Task Context 的 `prd.md`、`status.md`、`progress.md` 在 Phase 1 以 Plane DB 为 source of truth。
- Work Directory 与 Task Context Directory 已拆分：前者是代码执行目录，后者是任务上下文目录。
- Billing / Plan / Export 不属于目标产品主路径。

正在进行：

- PR #42：Agent / Prompt Library UI 可用化。
  - Agents / Prompts 页面接真实 workspace snapshot API。
  - 支持 Agent create / edit。
  - 支持 Prompt create / edit / archive / create version。
  - 支持 Agent prompt stack binding。
  - 已补中英文文案与前端测试，CI 正在运行。

## 改造总目标

第一阶段要让用户能完成一条真实软件交付链路：

```text
新建 Task
-> Intake / PRD 澄清
-> 选择 Work Directory 和 Agent
-> Development Agent 执行
-> Agent Review
-> Human Gate
-> Release
-> Human Gate
-> Deployment
-> Evidence 回流与复盘
```

验收时用户应从 Plane 看到三类事实：

- 谁在做：Agent、Prompt stack、Worker、Work Directory。
- 做到哪：workflow active node、Human Gate、Blocked/Failed node。
- 做成什么：PR、commit、checks、release image、deployment result、run conclusion。

## 产品主线

### 主线 1：Agent / Prompt 管理闭环

目标：用户能在 Plane 上配置“谁来做事、用什么 prompt 做事”。

必须完成：

- Agents 页面成为主导航下的一等页面，不藏在 Settings。
- Prompts 页面成为主导航下的一等页面，不藏在 Settings。
- Prompt 支持新增、编辑 metadata、archive、创建新版本。
- Agent 支持新增、编辑 runtime/model/defaults/is_default/is_active。
- Agent detail 能维护 ordered prompt stack。
- Prompt stack 读取规则清晰：Agent Prompt -> Project Prompt -> Role Prompt -> Playbook/Task Prompt -> business system Prompt。
- Agent / Prompt 列表默认展示当前 workspace 可见数据。

验收标准：

- 用户不看文档也能找到“新建 Agent”和“新建 Prompt”入口。
- 新建 Agent 后可以立即绑定一个或多个 Prompt。
- 绑定结果能在 Agent detail 中按顺序展示。
- 中英文界面文案完整。

### 主线 2：Worker / Work Directory 管理闭环

目标：用户能在 Plane 上配置“在哪台机器、哪个目录、哪些仓库里做事”。

必须完成：

- Workers 页面接真实 Worker Card API。
- Work Directories 页面接真实 Work Directory / Repository / Mount API。
- 一个 Work Directory 可绑定多个 repository。
- Project 可配置默认 Work Directory。
- Task 可 override Project 默认 Work Directory。
- Worker 选择由用户手动指定，默认继承 Project 配置。
- 页面只保存配置，不直接操作宿主机文件系统。

验收标准：

- 用户能看到当前可用 Worker、能力标签、挂载目录、活跃状态。
- 用户能为 Project 选择默认 Work Directory。
- 用户创建 Task 时默认继承 Project Work Directory，也可手动改。
- Run intent payload 能带 resolved work directory context。

### 主线 3：Task Intake 与上下文文档闭环

目标：每个 Task 先进入 To-do / Intake 节点，用户与 Agent 先把需求讲清楚。

必须完成：

- 新建 Task 默认创建 workflow instance，并进入 Intake 节点。
- 每个 Task 有自己的 Task Context Directory 逻辑对象。
- Task context 至少包含 `prd.md`、`status.md`、`progress.md`。
- `prd.md` 和 `status.md` 可以编辑。
- `progress.md` 必须 append-only。
- Development 之后如需修改 PRD，应把 Task 拖回 Intake 节点再改。
- Human comment 也要进入 Agent 可读 context snapshot。

验收标准：

- Task Detail 首屏能看到 `status.md`、`progress.md`、`prd.md`。
- Intake 节点能沉淀或编辑 PRD。
- Progress 追加记录可追溯，不允许静默覆盖。
- Agent run 前能读取最新 context snapshot。

### 主线 4：Task Detail / Workflow 控制闭环

目标：Task Detail 是单个任务的控制台，不是传统 issue 表单。

必须完成：

- Task Detail 展示 workflow chain。
- 节点展示 node type、mode、assigned agent、status、active marker。
- Agent 节点可打开运行详情、进度、结论和失败原因。
- Human Gate 节点支持 approve、return、set auto、set manual。
- Agent failed 后进入 Blocked 节点，等待人工补 context。
- 用户可以把 Task 从 Blocked 拖回某个目标节点。
- 未执行到的 Human Gate 也允许提前切到 auto。

验收标准：

- 用户打开 Task 就能知道当前卡在哪个节点。
- 用户能对 Human Gate 做明确操作，而不是只改一个 state。
- Agent 失败不会自动跳过，必须进入可见 Blocked。
- Plane native state 只作为兼容字段跟随 active node。

### 主线 5：Tasks Center 运行态首页

目标：首页从 Kanban 视角改为 Agent operations 视角。

必须完成：

- 首页优先显示 Waiting Human Gates。
- 首页显示 Blocked / Failed Agent Nodes。
- 首页显示 Running Agents。
- 首页显示 Active Tasks。
- 首页显示 Recent Progress。
- ToDo / Backlog / Kanban 只能作为辅助视图，不作为默认首屏。

验收标准：

- 用户一进来能看到“现在需要我处理什么”。
- Waiting gate 和 Failed node 有直接操作入口。
- Running agent 能跳到对应 Task / Node detail。

### 主线 6：ACP / Worker Evidence 回流闭环

目标：Plane 是控制台和计分板，ACP / Worker 负责真实执行并回写证据。

必须完成：

- Plane 生成 run intent。
- ACP 同步 Agent、Prompt、Worker、Work Directory、Task Context、Workflow 配置。
- Worker 在真实机器上执行，复用宿主机环境。
- ACP / Worker 回写 run progress、conclusion、Change Request、commit、checks、release image、deployment result。
- Evidence 在 Task Detail 和 Node Detail 中展示。
- 每次 Agent run 记录本次使用的 prompt stack 和 task context snapshot。

验收标准：

- 用户能从 Task Detail 打开 PR / commit / checks / release tag / image / deployment result。
- Release evidence 与 Deployment evidence 分开展示。
- Failed run 有明确失败原因和下一步建议。
- Evidence 可追加到 progress 或 artifact，不覆盖历史。

## 推荐 PR 顺序

### PR A：Agent / Prompt Library UI

状态：进行中，PR #42。

完成后要做：

- 等 CI 全绿。
- 合入 `preview`。
- tag 下一个 `plane-components-v*`。
- 发布镜像。
- 升级 MBP。
- 用真实浏览器验证 Agents / Prompts 页面能创建和编辑。

### PR B：Workers / Work Directories UI

范围：

- Worker list / detail。
- Work Directory list / detail。
- Repository / mount 管理。
- Project default Work Directory。
- Task override 入口的最小 UI。

不做：

- 远程安装 Worker。
- 直接读写宿主机目录。
- 复杂权限策略。

### PR C：Task Detail Context Shell

范围：

- Task Detail 接 Task Context Snapshot API。
- 展示 `status.md`、`progress.md`、`prd.md`。
- 支持编辑 `status.md` / `prd.md`。
- 支持追加 progress entry。
- 展示 human comments 区。

不做：

- 完整 workflow drag/drop。
- 完整 run logs viewer。

### PR D：Workflow Chain 与 Human Gate UI

范围：

- Task Detail workflow chain。
- Active node / node detail。
- Human Gate actions。
- Blocked return flow。
- Auto / manual toggle。

不做：

- Workflow template builder。
- 多 workflow 选择器。

### PR E：Tasks Center 首页

范围：

- Waiting Human Gates queue。
- Blocked / Failed Agent Nodes queue。
- Running Agents。
- Active Tasks。
- Recent Progress。
- 快速跳转到 Task / Node。

不做：

- 恢复传统 Kanban 为主入口。
- 高级筛选器。

### PR F：ACP Evidence Projection

范围：

- Run progress 回写。
- Run conclusion 回写。
- Change Request / commit / checks 回写。
- Release image / deployment result 回写。
- Task Detail / Node Detail evidence 展示。

不做：

- Plane 直接执行 Worker。
- Plane 保存 secret value。

## 工程门禁

每个功能 PR 必须满足：

- 从 `preview` 开 worktree 分支开发。
- 不直接 push main / preview。
- 保持 PR 范围小而可合入。
- 前端 PR 至少跑 `pnpm --filter web test`、`pnpm --filter web check:format`、`pnpm turbo run check:types --filter=web`。
- API PR 至少跑 contract tests、ruff、migration check。
- 文档同步：如果产品行为、API contract、部署方式变化，更新 `docs/agent-control-center-prd/`。
- 合入后通过 GitHub hosted CI 发布镜像。
- tag release 后升级 MBP，并验证公网入口。

## 部署验收

每个 release 部署到 MBP 后至少验证：

- `APP_RELEASE` 已切到新版本。
- 应用层镜像来自 `michaelxxx/plane-*:<version>`。
- migrator 正常退出。
- 公网 `http://80.251.222.30:3200/` 返回 200。
- 新增 API 未登录返回 401 或页面可访问，证明 route 已生效。
- 关键 UI 在桌面端和手机宽度下可用。

## 暂不做

Phase 1 暂不做：

- 多 workflow template picker。
- Prompt marketplace。
- 跨 workspace sharing。
- 细粒度权限与 secret value 安全方案。
- Plane 远程安装 Worker。
- Remote meta repo 定时同步。
- 复杂 BI 报表。

这些不进入当前执行链，避免主线被拆散。

## 下一步判定

PR #42 合入并部署后，下一刀应优先砍 **Workers / Work Directories UI**。

原因：

- Agent / Prompt 解决“谁做、怎么做”。
- Worker / Work Directory 解决“在哪做”。
- 这两块完成后，Task Detail 才能真正把 Agent、Prompt、Worker、Work Directory、Context、Workflow 串成可执行链。
