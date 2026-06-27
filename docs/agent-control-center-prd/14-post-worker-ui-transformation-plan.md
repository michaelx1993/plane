# PR B 之后的改造计划

Status: Draft for execution
Last updated: 2026-06-27
Baseline: PR #44 merged, `plane-components-v0.0.29` release pending

本文档回答 PR B 合入后，下一阶段应该继续改造什么。目标是把当前已经具备的 Agent、Prompt、Worker、Work Directory 底座串成一个 task-centered agent operations 产品闭环。

## 当前状态

已经具备：

- Agent / Prompt Library UI：用户可以看到并维护 Agent 和 Prompt。
- Workers / Work Directories UI：用户可以维护 Worker、Work Directory、Repository、Mount。
- Project Settings：项目可以配置默认 Work Directory 和 Worker。
- Task Agent Run panel：任务执行前可以覆盖 Work Directory。
- 后端表与 API：Agent、Prompt、Worker、Work Directory、Task Context、Workflow Instance、Human Gate 已有第一版底座。

仍未形成完整体验：

- Task Detail 仍不是 Agent 执行控制台。
- `prd.md`、`status.md`、`progress.md` 尚未成为 task 首屏核心内容。
- Workflow chain 和 Human Gate 还没有真实可操作 UI。
- Agent run evidence 尚未从 ACP / Worker 回流到 Task Detail。
- Tasks Center 还没有从传统 issue list 改成 attention queue。

## 改造原则

- Plane 是入口、控制台和计分板；ACP / Worker 负责真实执行。
- Task 是用户操作中心；Project 只提供归组、默认配置和策略。
- Workflow active node 是主事实；Plane native state 只是兼容派生字段。
- Work Directory 是代码执行上下文；Task Context Directory 是任务文档上下文。
- Human Gate 默认 manual，但每个 task / node 可以切为 auto。
- Agent 节点失败后进入 Blocked，等待人工补充上下文后再拖回指定节点。

## 下一阶段 PR 顺序

### PR C：Task Detail Context Shell

目标：先把 Task Detail 改成任务控制台的骨架。

范围：

- 在 Task Detail 首屏展示 `status.md`、`progress.md`、`prd.md`。
- 接 Task Context Snapshot API。
- 支持编辑 `status.md`。
- 支持在 Intake 节点编辑 `prd.md`。
- 支持追加 `progress.md` entry，不允许直接覆盖历史 progress。
- 展示 Human Context / comments 区，作为下一次 Agent run 可读取的补充上下文。
- 在 Header 展示 active workflow node、owner、selected Work Directory、selected Worker。

验收标准：

- 用户打开 task 后第一眼看到的是当前事实状态、进度和 PRD，而不是传统 issue 字段。
- `progress.md` 只能追加。
- Development 之后修改 PRD 的入口必须引导用户回到 Intake 节点。
- Agent run 前可以读取最新 task context snapshot。

暂不做：

- 完整 workflow drag/drop。
- 完整 run logs viewer。
- Evidence 详情页。

### PR D：Workflow Chain 与 Human Gate UI

目标：让用户能从 Task Detail 操作流程节点。

范围：

- 展示默认软件交付 workflow chain。
- 节点展示 type、mode、status、assigned Agent、active marker。
- Agent node 展示 running / success / failed / blocked 状态。
- Human Gate 支持 approve、return、set auto、set manual。
- Blocked 节点支持补充 context 后拖回 Development / Review / Release / Deployment 等目标节点。
- Plane native state 跟随 active workflow node 派生同步。

验收标准：

- 用户能明确看到 task 当前卡在哪个节点。
- Human Gate 不再只是改 state，而是有显式操作。
- Agent failed 后进入 Blocked，不自动 skip。
- 未执行到的 Human Gate 也能提前切换 auto / manual。

暂不做：

- 多 workflow template picker。
- Workflow template builder。
- 模板市场。

### PR E：Tasks Center 运行态首页

目标：把首页从传统看板改成 Agent operations attention queue。

范围：

- Waiting Human Gates queue。
- Blocked / Failed Agent Nodes queue。
- Running Agents。
- Active Tasks。
- Recent Progress。
- 每个队列项都能跳到对应 Task / Node。
- 旧 ToDo / Backlog / Kanban 作为辅助入口保留或弱化，不再作为默认视角。

验收标准：

- 用户一进来就知道现在需要自己处理什么。
- Waiting gate 和 failed node 有直接操作入口。
- Running agent 能直接打开 run / node detail。
- 桌面端和手机端都能扫描关键队列。

暂不做：

- 复杂 BI 报表。
- 多维度资源利用率分析。

### PR F：ACP / Worker Evidence Projection

目标：让真实执行结果回流到 Plane，形成闭环。

范围：

- Plane 生成 run intent 后，ACP 读取 Agent、Prompt stack、Worker、Work Directory、Task Context、Workflow node。
- ACP / Worker 回写 run progress、run conclusion、failure reason。
- 回写 Change Request、commit、checks、release tag/image、deployment result。
- Task Detail 和 Node Detail 展示 evidence。
- 每次 run 记录本次使用的 prompt stack 和 task context snapshot。

验收标准：

- 用户能从 Task Detail 打开 Change Request / commit / checks / release image / deployment result。
- Release evidence 和 Deployment evidence 分开展示。
- Failed run 有明确失败原因、最后日志摘要和建议补充的 context。
- Evidence 可以追加到 progress 或 artifact，不覆盖历史。

暂不做：

- Plane 直接执行 Worker。
- Plane 保存 secret value。
- Worker 远程安装和升级。

## UI 信息架构调整

主导航应该向 Agent 托管中心收敛：

```text
Agent Center
  Home / Attention Queue
  Tasks
  Agents
  Prompts
  Workflows
  Workers
  Work Directories
  Settings
```

Task Detail 应该成为最重要的单体页面：

```text
Task Detail
  Header: title / active node / owner / work directory / primary action
  Status: rendered status.md
  Progress: append-only progress.md
  PRD: rendered prd.md
  Workflow Chain: nodes / active detail / actions
  Human Context: comments and corrections
  Artifacts: CR / commit / checks / release / deployment
```

## 数据与集成约束

- Plane DB 维护用户可编辑配置和 task context source of truth。
- ACP 通过强连接或轮询同步 projection；Phase 1 可以先用轮询。
- Worker 复用宿主机环境执行，不由 Plane 远程安装。
- Secret 是用户级密码本概念；Plane 第一阶段只传递 key 名称和引用，不把 secret value 写入 progress、evidence 或日志。
- Prompt 生效版本由 Prompt Version policy 决定；Agent 绑定 prompt，不在 Agent 内单独选择历史版本。

## 里程碑

### Milestone 1：Task 可读

完成 PR C。用户能在 Task Detail 看清状态、进度、PRD 和当前执行上下文。

### Milestone 2：Task 可控

完成 PR D。用户能 approve / return / auto gate / 从 Blocked 拖回目标节点。

### Milestone 3：首页可用

完成 PR E。用户进入 Plane 后优先处理等待人工介入和失败节点。

### Milestone 4：执行闭环

完成 PR F。ACP / Worker 的真实执行证据回流到 Plane，Task Detail 成为完整控制台。

## 近期不进入范围

- 多 workflow 模板选择。
- Workflow builder。
- Prompt marketplace。
- Remote meta repo 定时同步。
- 细粒度 RBAC。
- Billing / Plan。
- Export。
- Plane 远程安装 Worker。

这些能力不应阻塞 Phase 1 的 Agent 托管闭环。
