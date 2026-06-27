# Agent Library 与 Prompt Library

## Agent Library

Agent Library 管理可复用 Agent。它回答“谁来做事、默认怎么做、用哪些 Prompt、跑在哪个 Worker、能处理哪些节点”。

页面结构：

```text
Agent Library
  Agent list
    search / filter
    owned by me
    active / archived

  Agent detail
    profile
    prompt stack
    default role
    default worker
    allowed tools
    workflow node bindings
    recent runs
```

Agent list 每行展示：

- Agent name
- description / role summary
- default role
- default Worker
- prompt count
- recent run status
- active / archived

Agent detail 展示：

- name、description、status、owner
- Prompt Stack：prompt、scope、kind、order、version policy、pinned version
- default model / reasoning / worker
- allowed tools：read files、write files、run tests、create Change Request、release、deploy
- workflow node bindings：Intake、Development、Code Review、Release、Deployment 等
- recent runs、失败原因、结论和 artifacts

## Agent 创建/编辑

- 可以选择一个或多个 Prompt。
- Prompt 组合是 append/stack，不是覆盖。
- 可以设置 default role 和适用 workflow node。
- 可以设置 default worker。
- Phase 1：Agent user-owned、workspace-visible，不做复杂共享权限。

## Agent 选择规则

Task 可以设置 default Agent；每个 workflow node 也可以单独 override Agent。

选择优先级：

```text
node-level assigned Agent
-> task default Agent
-> project default Agent
-> system default general-purpose Agent
```

Agent Library 需要展示 Agent 适合哪些 workflow nodes，方便用户在 task 或 node 上选择。

## Prompt Library

Prompt Library 管理可复用 Prompt。它回答“Agent 启动时读哪些指令、上下文、约束、workflow 规则和输出契约”。

页面结构：

```text
Prompt Library
  Prompt list
    search / filter
    scope
    kind
    status

  Prompt detail
    metadata
    latest version
    version history
    bindings
    preview
```

Prompt list 每行展示：

- Prompt name
- scope：agent / project / role / playbook / task / workspace
- kind：instruction / context / constraint / workflow / style / safety / output-contract
- latest version
- bound agents count
- status：draft / active / archived

Prompt detail 展示：

- metadata：name、description、scope、kind、visibility、status
- latest version body
- version history：version、author、changelog、created_at、content hash
- bindings：哪些 Agent、Project、Role 或 Workflow node 正在使用
- preview：渲染变量后的 prompt 片段

## Prompt 操作

- Create prompt
- Edit prompt metadata
- Create new prompt version
- Archive prompt
- 查看引用关系

删除规则：

- Phase 1 默认 soft delete / archive。
- 已被历史 run 使用的 prompt version 不删除。
- Prompt 从库里移除后，不影响历史 task、run、prompt release。
