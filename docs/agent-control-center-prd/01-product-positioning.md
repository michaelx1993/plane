# 产品定位

## 一句话

**Agent 托管与流程控制中心**。

这不是一个带 Agent 插件的项目管理工具，而是一个围绕 Agent 托管、任务执行、workflow 控制和 Human Gate 组织的操作中心。

## 首要问题

产品首先要回答：

- 我有哪些 Agent 可以用？
- 每个 Agent 可以使用哪些 Prompt、Role、Worker、Work Directory、Repository 和 Secret？
- 哪个 Task 分配给了哪个 Agent？
- 当前 Task 执行到哪个 workflow node？
- 哪个 Agent node 正在运行或失败？
- 哪个 Human Gate 正在等待我处理？
- Agent 做了什么、结论是什么、产物在哪里？

## Plane 的角色

不要推倒 Plane。Phase 1 复用 Plane 的基础壳层：

- login
- workspace / project
- work item 容器
- member / permission
- API key
- webhook
- self-host deployment

但产品主模型不再是 Plane 原生 state、Backlog、ToDo 或 Kanban board。

## 一等对象

- `Agent`：谁来做事。
- `Prompt`：Agent 启动时读取的可复用指令、上下文、约束和输出契约。
- `Worker`：Agent 运行在哪台真实机器或 runtime 上。
- `Work Directory`：Agent 执行代码任务的本地工作目录，可包含多个 repositories。
- `Workflow Instance`：每个 task 自己的执行链。
- `Run`：Agent 在某个节点上的一次执行实例。
- `Human Gate`：需要人工确认、打回、放行或设为 auto 的节点。
- `Evidence`：Change Request、commit、release、deployment、logs、summary。

## 非核心对象

以下 Plane 原生对象只作为兼容面或次级过滤，不主导首屏体验：

- native state
- Backlog / ToDo
- board columns
- cycles
- modules
- generic project-management settings

## 移除/隐藏

- Billing / Plan
- Export
