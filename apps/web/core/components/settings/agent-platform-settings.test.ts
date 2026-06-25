/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const appRoot = path.resolve(import.meta.dirname, "../../..");
const repoRoot = path.resolve(appRoot, "../..");

const routeSource = read("apps/web/app/routes/core.ts");
const workspaceSettingsSource = read("packages/constants/src/settings/workspace.ts");
const projectSettingsSource = read("packages/constants/src/settings/project.ts");
const workspacePageSource = read("apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/agents/page.tsx");
const projectPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(settings)/settings/projects/[projectId]/agents/page.tsx"
);
const issueWidgetActionSource = read("apps/web/core/components/issues/issue-detail-widgets/action-buttons.tsx");
const agentRunActionSource = read("apps/web/core/components/issues/issue-detail-widgets/agent-run-action-button.tsx");
const serviceSource = read("apps/web/core/services/agent-platform.service.ts");

assert.ok(routeSource.includes(":workspaceSlug/settings/agents"), "workspace Agent Library route should be registered");
assert.ok(
  routeSource.includes(":workspaceSlug/settings/projects/:projectId/agents"),
  "project Agents route should be registered"
);
assert.ok(
  workspaceSettingsSource.includes('key: "agents"') &&
    workspaceSettingsSource.includes("href: `/settings/agents`") &&
    workspaceSettingsSource.includes('WORKSPACE_SETTINGS["agents"]'),
  "workspace settings should expose an Agent Library navigation item"
);
assert.ok(
  projectSettingsSource.includes('key: "agents"') &&
    projectSettingsSource.includes("href: `/agents`") &&
    projectSettingsSource.includes('PROJECT_SETTINGS["agents"]'),
  "project settings should expose a Project Agents navigation item"
);
assert.ok(
  serviceSource.includes("getWorkspaceSnapshot") &&
    serviceSource.includes("agent-agents") &&
    serviceSource.includes("agent-prompt-bindings") &&
    serviceSource.includes("agent-user-secret-keys"),
  "agent platform service should cover workspace agent resources"
);
assert.ok(
  serviceSource.includes("getProjectSnapshot") &&
    serviceSource.includes("agent-worker-cards") &&
    serviceSource.includes("agent-repositories") &&
    serviceSource.includes("createRunIntent") &&
    serviceSource.includes("agent-runs"),
  "agent platform service should cover project agent resources"
);
assert.ok(
  serviceSource.includes("{ validateStatus: null }") &&
    serviceSource.includes("response?.status === 401 || response?.status === 403") &&
    serviceSource.includes("return [];"),
  "agent platform snapshot reads should not trigger global auth redirects when optional config APIs deny access"
);
assert.ok(
  workspacePageSource.includes("createAgent") &&
    workspacePageSource.includes("createPromptVersion") &&
    workspacePageSource.includes("createPromptBinding") &&
    workspacePageSource.includes("createSecretKey") &&
    workspacePageSource.includes("version_policy") &&
    workspacePageSource.includes("scope") &&
    workspacePageSource.includes("kind"),
  "workspace Agent Library page should create agents, prompt versions, bindings, and secret keys"
);
assert.ok(
  projectPageSource.includes("createWorkerCard") &&
    projectPageSource.includes("createProjectWorkspace") &&
    projectPageSource.includes("createRepository") &&
    projectPageSource.includes("meta_git_mode") &&
    projectPageSource.includes("credential_key") &&
    projectPageSource.includes("worktree_strategy"),
  "project Agents page should create worker cards, PRD workspace config, and repositories"
);
assert.ok(
  issueWidgetActionSource.includes("AgentRunActionButton"),
  "work item detail widgets should expose the Agent run action"
);
assert.ok(
  agentRunActionSource.includes("getWorkspaceSnapshot") &&
    agentRunActionSource.includes("getProjectSnapshot") &&
    agentRunActionSource.includes("issue.agent_run.title") &&
    !agentRunActionSource.includes('type="checkbox"') &&
    !agentRunActionSource.includes("peer-checked:block") &&
    agentRunActionSource.includes("isMounted") &&
    agentRunActionSource.includes("if (!isMounted) return null") &&
    agentRunActionSource.includes("isMounted ? `AGENT_RUN_WORKSPACE_") &&
    agentRunActionSource.includes("isMounted ? `AGENT_RUN_PROJECT_") &&
    agentRunActionSource.includes('data-testid="agent-run-action-trigger"') &&
    agentRunActionSource.includes("promptStack") &&
    agentRunActionSource.includes("availableSecretKeys") &&
    agentRunActionSource.includes("submitRunIntent") &&
    agentRunActionSource.includes("createRunIntent") &&
    agentRunActionSource.includes("copyRunIntent"),
  "Agent run action should expose a resilient trigger, assemble Agent context, and queue run intents"
);

for (const locale of ["en", "zh-CN", "zh-TW"]) {
  const workspaceMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/workspace-settings.json`));
  const projectMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/project-settings.json`));
  const workItemMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/work-item.json`));
  assert.ok(workspaceMessages.workspace_settings.settings.agents.title, `${locale} workspace agent title is required`);
  assert.ok(projectMessages.project_settings.agents.label, `${locale} project agent label is required`);
  assert.ok(workItemMessages.issue.agent_run.action, `${locale} work item Agent run action is required`);
  assert.ok(workItemMessages.issue.agent_run.start, `${locale} work item Agent run start is required`);
  assert.ok(workItemMessages.issue.agent_run.queued, `${locale} work item Agent run queued is required`);
}

console.log("agent_platform_settings=passed");

function read(relativePath: string): string {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf-8");
}
