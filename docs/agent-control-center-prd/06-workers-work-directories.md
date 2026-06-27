# Workers、Work Directories 与 Repositories

## Workers

Workers 是真实执行环境管理页面。它回答“Agent 跑在哪台机器、当前是否可用、能访问哪些能力”。

页面结构：

```text
Workers
  Worker cards
    status
    host
    capabilities
    current runs

  Worker detail
    environment
    allowed work directories / repositories
    default agents
    recent runs
    health / heartbeat
```

Worker card 展示：

- name，例如 Mac Studio Worker、MBP Worker、Remote Linux Worker
- status：online / offline / draining / disabled
- host label / environment
- capabilities：shell、git、docker、release、deploy、browser、mobile
- current run count
- last heartbeat

Worker detail 展示：

- runtime profile
- host notes
- capabilities and limits
- default work directory / worktree policy
- accessible work directories / repositories
- default Agent or workflow node bindings
- recent runs
- failure reason
- last heartbeat

Phase 1 约束：

- Worker 在 Plane 中是可编辑配置和可见卡片。
- heartbeat、claim、lease、真实运行状态由 ACP/worker runtime 管理。
- Plane 不保存 worker token secret value，只展示 key metadata 或引用。

## Work Directories

Work Directory 是 Agent 执行代码任务的上下文入口。Phase 1 软件交付任务默认绑定一个已注册 work directory，而不是只绑定单个 repository。

一个 work directory 可以包含一个或多个 repositories，用于支持：

- 单仓开发
- 多仓开发
- monorepo 子目录开发
- 跨仓联动任务

## Task 与 Work Directory 绑定

每个项目可以配置一个默认 Work Directory。新建 task 时默认使用项目的 Work Directory，但用户可以在 task 创建或编辑时覆盖为其它 Work Directory。

执行时：

```text
Task -> selected Work Directory -> selected Worker -> Worker local path / mount
```

也就是说，Task 绑定的是逻辑 Work Directory；真正本地路径由 Worker 上的 mount/local path 配置解析。

示例：

```text
Work Directory: plane-agent-stack
  repositories:
    plane -> ./plane
    agent-control-plane -> ./agent-control-plane

Worker mounts:
  Mac Studio -> /Users/a/aiworkspace/plane-agent-stack
  MBP        -> /Users/a/work/plane-agent-stack
```

这样一个 task 可以默认继承项目目录，也可以临时改到其它目录；同一个 Work Directory 在不同 Worker 上可以有不同真实路径。

页面结构：

```text
Work Directories
  Work Directory list
    local path
    owner project
    repositories count
    worker access

  Work Directory detail
    root path
    repositories
    default worker
    branch / worktree policy
    prd.md / status.md / progress.md mirror policy
    recent tasks

Repositories
  Repository registry
    provider
    full name
    local relative path
    credential key
```

Work Directory list 每行展示：

- name
- root path
- repositories count
- default worker
- active task count
- last used

Work Directory detail 展示：

- root path
- repositories
- repository relative paths
- default worker and allowed workers
- worker mount/local path mapping
- worktree strategy：per-task worktree、branch checkout、readonly
- branch policy：default branch、target branch override
- prd/status/progress mirror policy
- recent tasks、Change Requests、release/deploy evidence

Repository registry 每行展示：

- provider：GitHub / GitLab / local / other
- full name
- local relative path
- default branch
- credential key name

操作：

- register work directory
- register repository under directory
- edit credential key / default branch / relative path / worktree strategy
- bind work directory to project
- mark inactive

Phase 1 约束：

- 软件开发类 task 必须选择 work directory。
- 单仓 task 是 work directory 下只有一个 repository 的特例。
- repo-less task 不进入第一期默认交付链。
- UI 使用 `Change Request`，不要写死 GitHub PR。
