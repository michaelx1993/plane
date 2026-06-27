# Phase 1 实施分期

Phase 1 不一次性重写整个 Plane。按可上线闭环拆成 6 个里程碑。

## Milestone 1：产品入口收敛

范围：

- 隐藏 Billing/Plan。
- 隐藏 Export。
- 主导航新增 Tasks、Agents、Prompts、Workers、Work Directories。
- 弱化 Projects/Views/Cycles/Modules/Backlog/ToDo 的首屏存在感。
- 登录后默认进入 Tasks Center。

验收：

- 用户首屏看到 Agent 托管与流程控制中心，而不是 Kanban/state board。
- 用户能从主导航进入 Agent、Prompt、Worker、Work Directory 管理。

## Milestone 2：Agent / Prompt 管理面

范围：

- 重构当前 Agent Library 表单堆叠 UI。
- 拆成 Agent Library 和 Prompt Library。
- Prompt 支持 create / view / edit / archive。
- Agent 支持 create / view / edit。
- Agent 可以选择多个 Prompt 组成 prompt stack。
- 展示 Agent 的 default role、default worker、workflow node bindings。

验收：

- 用户可以在页面上新建 Agent。
- 用户可以在页面上新建、编辑、归档 Prompt。
- 用户可以看到 Agent 绑定了哪些 Prompt。

## Milestone 3：Worker / Work Directory 管理面

范围：

- Workers 页面展示 worker card、status、capabilities、heartbeat、recent runs。
- Work Directories 页面支持注册 work directory。
- Work Directory 下支持登记一个或多个 repositories。
- Repository 支持 provider、full name、relative path、default branch、credential key。
- Agent / task 可以引用 default worker 和 work directory。

验收：

- 用户能看到 Mac Studio / MBP 等 worker。
- 用户能登记一个多仓 work directory。
- 新 task 能选择 work directory。

## Milestone 4：Tasks Center 和 Task Detail

范围：

- 登录后默认进入 Tasks Center。
- Tasks Center 展示 Waiting Human Gates、Failed Agent Nodes、Running Agents、Active Tasks、Recent Progress。
- Task Detail 展示 prd.md、status.md、progress.md、workflow chain、human comments、artifacts。
- prd.md / status.md / progress.md source of truth 存 Plane DB。
- progress.md 使用 append-only entries 渲染。

验收：

- 用户点开 task 后先看到 status，再看到 progress。
- 用户能看到 task 当前 active workflow node。
- 人工评论能作为 Agent 可读 task context 保存。

## Milestone 5：Workflow Instance 和 Human Gate

范围：

- 新 task 自动挂 Phase 1 默认 Agent software delivery workflow instance。
- workflow active node 派生同步到 Plane native state 兼容字段。
- Human Review / Human Gate 默认 manual。
- Human Gate 支持 approve、return、set auto。
- Agent 失败进入 Blocked / exception node。
- Blocked task 支持人工补充 context 后拖回指定 workflow node。

验收：

- 用户能在 task 详情里操作 Human Gate。
- Agent node failed 后不会自动继续，会进入 Blocked。
- 用户补充上下文后能把 task 送回 Development 或其它合适节点。

## Milestone 6：ACP Run Evidence 集成

范围：

- Agent node 展示 ACP run detail。
- 展示 prompt stack / prompt release。
- 展示 run progress、logs、conclusion。
- 展示 Change Request、commit、release、deployment evidence。
- ACP/Agent 读取 prd.md、status.md、progress.md、human comments 作为 task context。

验收：

- 用户能从 Agent 节点看到 Agent 做了什么、结论是什么、产物在哪里。
- 下一次 Agent run 能读到人工补充的 context。
- Plane 控制台、ACP run、worker progress 三者状态一致。
