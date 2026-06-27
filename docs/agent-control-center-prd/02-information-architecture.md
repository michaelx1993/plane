# 信息架构与首页

## 主导航

主导航围绕 Agent 控制模型组织：

```text
Tasks
Agents
Prompts
Workflows
Workers
Work Directories
Settings
```

`Projects`、`Views`、`Cycles`、`Modules`、`Backlog`、`ToDo` 不应主导首屏。

## 默认首页：Tasks Center

登录后默认进入 `Tasks Center`，它是运行态中心，不是 Kanban board。

首屏结构：

```text
Tasks Center
  Top Metrics
    Running Agents
    Waiting Human Gates
    Failed / Blocked Nodes
    Active Tasks

  Attention Queue
    Human Gates waiting for me
    Failed Agent nodes
    Blocked tasks

  Active Task List
    Task
    Active workflow node
    Assigned Agent / Worker
    Last progress
    Next required action

  Recent Progress
    Agent conclusions
    Human decisions
    Release / deployment evidence
```

## 默认排序

1. Waiting Human Gates
2. Failed / Blocked Agent nodes
3. Running Agent nodes that are stale or timed out
4. Normal active tasks
5. Recently completed tasks

## Task 行信息

每行 task 直接展示：

- task title / identifier
- active workflow node
- node state：running / waiting_for_human / failed / blocked / passed
- owner：Agent / Human / System
- assigned Agent
- assigned Worker
- last progress summary
- next action：review / add context / return / approve / open run detail

## 首页动作

- 新建 task
- 新建 Agent
- 新建 Prompt
- 查看 Waiting Human Gates
- 查看 Failed Agent Nodes
- 打开 task detail
- 对 Human Gate 执行 approve / return / set auto
- 对 Blocked task 补充 context 后拖回指定 workflow node

## 新建 Task 后的入口

新建 task 后进入 `To-do / Intake / PRD` 节点。这里不是传统 Backlog/ToDo 状态列，而是用户和 Intake Agent 对话澄清需求的地方。

首页应把处于 Intake 的 task 展示为“需求澄清中”或 “Intake in progress”，而不是普通待办。

## Secondary Filters

- project
- work directory / repository
- assigned Agent
- Worker
- workflow node
- blocked / waiting / running / completed
