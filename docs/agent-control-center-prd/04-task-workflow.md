# 默认 Workflow 与节点规则

## 模型

Plane 不使用一个全局状态机作为产品模型。主模型是：

```text
Workflow Template -> Task Workflow Instance
```

Phase 1 只提供一个内置默认模板：Agent software delivery workflow。新建 task 时自动复制一份 workflow instance 到该 task。

不做：

- workflow template picker
- workflow template builder
- 多模板市场

未来可以支持文档、运维、调研、standalone shell/script 等模板。

## Phase 1 默认节点

| Order | Node | Type | Default owner | Default mode | Main exits |
| --- | --- | --- | --- | --- | --- |
| 1 | To-do / Intake / PRD | `intake` | Intake Agent + Human | conversational, then auto | Development, Blocked, Done |
| 2 | Development | `agent` | Builder Agent | auto | Code Review, Blocked |
| 3 | Code Review / Agent Review | `agent_review` | Reviewer Agent | auto | Human Review, Development, Blocked |
| 4 | Human Review | `human_review` | Human | manual | In Merge, Development, Done, Blocked |
| 5 | In Merge | `merge` | Merge Agent | auto after human approval | Merged, Development, Blocked |
| 6 | Merged Gate | `human_gate` | Human | manual, can be set auto per task | Release Version, Development, Done, Blocked |
| 7 | Release Version | `release` | Release Agent | auto after gate | Released, Development, Blocked |
| 8 | Released Gate | `human_gate` | Human | manual, can be set auto per task | Deployment, Development, Done, Blocked |
| 9 | Deployment | `deploy` | Deploy Agent | auto after gate | Deployed, Development, Blocked |
| 10 | Deployed Gate | `human_gate` | Human | manual, can be set auto per task | Done, Development, Blocked |
| 11 | Done | `terminal` | System | terminal | none |

## 角色路由

```text
To-do / Intake / PRD -> Intake Agent + Human
Development           -> Builder Agent
Code Review           -> Reviewer Agent
Human Review          -> Human Gate
In Merge              -> Merge Agent
Merged Gate           -> Human Gate
Release Version       -> Release Agent
Released Gate         -> Human Gate
Deployment            -> Deploy Agent
Deployed Gate         -> Human Gate
Done                  -> terminal
```

## Agent 分配与 Override

Task 可以有一个默认 Agent。默认 Agent 用作未显式配置节点的兜底执行者。

每个 workflow node 都允许 override Agent：

- Development 可指定 Builder Agent。
- Code Review 可指定 Reviewer Agent。
- In Merge 可指定 Merge Agent。
- Release Version 可指定 Release Agent。
- Deployment 可指定 Deploy Agent。
- Intake 可指定 Intake Agent。

优先级：

```text
node-level assigned Agent
-> task default Agent
-> project default Agent
-> system default general-purpose Agent
```

Node override 只影响当前 task workflow instance，不修改默认 workflow template。

## To-do / Intake 节点

新建 task 后先进入 `To-do / Intake / PRD` 节点。这个节点不是传统项目管理里的待办状态，而是人与 Agent 共同澄清背景、沉淀需求文档的对话节点。

目标：

- 用户和 Intake Agent 对话，补充项目背景、目标、约束和验收标准。
- Intake Agent 持续整理 `prd.md`，形成可执行的需求文档。
- Intake Agent 同步维护 `status.md` 中的当前事实状态。
- Intake Agent 识别缺失信息、依赖、权限、secret、环境和外部决策。
- 当需求足够清楚时，Intake Agent 建议进入 `Development`。
- 如果缺少外部输入，则进入 `Blocked`。
- 默认情况下，To-do / Intake 结束需要用户点击“开始开发”确认进入 `Development`。
- 用户可以把当前 task 的 Intake 节点设为 auto；auto 模式下，Intake Agent 判断 PRD 已足够可执行后可以进入 `Development`。

To-do / Intake 节点的完成门槛：

- `prd.md` 中有清晰目标。
- 有 acceptance criteria。
- 有 work directory / repository context。
- 有 validation requirements。
- 有必要的 constraints / non-goals。
- 用户确认可以开始开发，或 Intake 节点已设为 auto 且 Intake Agent 判断可执行。

这个节点允许多轮对话，不要求一次性填完复杂表单。

## PRD 修改规则

`prd.md` 可以修改，但 PRD 修改必须回到 `To-do / Intake / PRD` 节点进行。

规则：

- Development 或后续节点中如果发现 PRD 需要改，用户应把 task 退回 `To-do / Intake / PRD`。
- 在 Intake 节点完成 PRD 修订、补充背景和重新确认 acceptance criteria。
- PRD 修订完成后，再由用户点击“开始开发”或通过 Intake auto 进入 Development。
- 不允许在 Development、Review、Release、Deployment 等后续节点静默修改 PRD 并继续执行。
- 每次 PRD 修改都应产生版本记录和 progress entry。

## Human Gate

- 所有 Human Review / Human Gate 默认 manual。
- 用户可以把当前 task 的某个 Human Gate 改成 auto。
- Phase 1 的 auto 只影响当前 task workflow instance，不写回默认模板。

## Agent 失败

- Agent-owned node 失败后，该节点标记 `failed`。
- Task 进入 `Blocked` / exception node。
- Phase 1 不自动 retry、skip 或继续下一步。
- 人工先补充 context / correction / feedback，再拖回合适节点。
- 常见回退目标是 Development，但可以回 Intake、Review、Release 或 Deployment。
- 人工补充内容必须进入下一次 Agent run 的 task context。

## 允许短路

```text
Human Review -> Done
Merged Gate -> Done
Released Gate -> Done
Deployed Gate -> Done
```

## 允许返工

```text
Code Review -> Development
Human Review -> Development
Merged Gate -> Development
Released Gate -> Development
Deployed Gate -> Development
```

## 允许阻塞

```text
any non-terminal node -> Blocked
Blocked -> Development
Blocked -> Human Review
Blocked -> Merged Gate
Blocked -> Released Gate
Blocked -> Deployed Gate
```

## Plane Native State 兼容

Workflow active node 是主事实。Plane native state 只是派生兼容字段，用于旧 API、webhook、过滤和部分组件。

规则：

- 用户和 Agent 操作 workflow node。
- active workflow node 自动同步到 native state。
- 旧 UI 里直接改 state 的入口应隐藏或禁用。
- 如果必须保留旧 state API，必须走 workflow transition validation。
- state 不保存业务证据，证据在 workflow node、status.md、progress.md 和 artifacts 里。
