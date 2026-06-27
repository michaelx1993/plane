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
const workspaceMenuSource = read("apps/web/core/components/workspace/sidebar/workspace-menu.tsx");
const workspaceNavigationSource = read("packages/constants/src/workspace.ts");
const appSidebarSource = read("apps/web/app/(all)/[workspaceSlug]/(projects)/sidebar.tsx");
const sidebarItemSource = read("apps/web/core/components/workspace/sidebar/sidebar-item.tsx");
const sidebarWrapperSource = read("apps/web/core/components/sidebar/sidebar-wrapper.tsx");
const sidebarIconSource = read("apps/web/ce/components/workspace/sidebar/helper.tsx");
const workspaceSettingsSource = read("packages/constants/src/settings/workspace.ts");
const projectSettingsSource = read("packages/constants/src/settings/project.ts");
const workspacePageSource = read("apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/agents/page.tsx");
const workspaceMembersPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/members/page.tsx"
);
const projectPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(settings)/settings/projects/[projectId]/agents/page.tsx"
);
const agentCenterAgentsPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(projects)/agent-control-center/agents/page.tsx"
);
const agentCenterPromptsPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(projects)/agent-control-center/prompts/page.tsx"
);
const agentCenterWorkersPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(projects)/agent-control-center/workers/page.tsx"
);
const agentCenterWorkDirectoriesPageSource = read(
  "apps/web/app/(all)/[workspaceSlug]/(projects)/agent-control-center/work-directories/page.tsx"
);
const agentCenterLibraryPageSource = read(
  "apps/web/core/components/agent-control-center/agent-prompt-library-page.tsx"
);
const agentCenterWorkerDirectoryPageSource = read(
  "apps/web/core/components/agent-control-center/worker-directory-page.tsx"
);
const issueWidgetActionSource = read("apps/web/core/components/issues/issue-detail-widgets/action-buttons.tsx");
const agentRunActionSource = read("apps/web/core/components/issues/issue-detail-widgets/agent-run-action-button.tsx");
const serviceSource = read("apps/web/core/services/agent-platform.service.ts");

assert.ok(routeSource.includes(":workspaceSlug/settings/agents"), "workspace Agent Library route should be registered");
assert.ok(
  routeSource.includes(
    'route(":workspaceSlug", "./(all)/[workspaceSlug]/(projects)/agent-control-center/home/page.tsx")'
  ),
  "workspace root should open the Agent Control Center Tasks page"
);
for (const routePath of [
  ":workspaceSlug/tasks",
  ":workspaceSlug/agents",
  ":workspaceSlug/prompts",
  ":workspaceSlug/workflows",
  ":workspaceSlug/workers",
  ":workspaceSlug/work-directories",
]) {
  assert.ok(routeSource.includes(routePath), `${routePath} Agent Control Center route should be registered`);
}
assert.ok(
  routeSource.includes(":workspaceSlug/settings/projects/:projectId/agents"),
  "project Agents route should be registered"
);
for (const sidebarKey of [
  "sidebar.tasks",
  "sidebar.agents",
  "sidebar.prompts",
  "sidebar.workflows",
  "sidebar.workers",
  "sidebar.work_directories",
]) {
  assert.ok(workspaceMenuSource.includes(sidebarKey), `${sidebarKey} should be exposed in the workspace sidebar`);
}
assert.ok(
  !workspaceMenuSource.includes("sidebar.views") &&
    !workspaceMenuSource.includes("sidebar.cycles") &&
    !workspaceMenuSource.includes("sidebar.analytics"),
  "workspace sidebar should prioritize Agent Control Center entries instead of Plane views, cycles, and analytics"
);
for (const agentCenterKey of ["tasks", "agents", "prompts", "workflows", "workers", "work-directories"]) {
  assert.ok(
    workspaceNavigationSource.includes(`WORKSPACE_SIDEBAR_DYNAMIC_NAVIGATION_ITEMS["${agentCenterKey}"]`),
    `${agentCenterKey} should be in the active workspace navigation constants`
  );
  assert.ok(sidebarItemSource.includes(`"${agentCenterKey}"`), `${agentCenterKey} should render without pin state`);
}
assert.ok(
  appSidebarSource.includes('title="Agent Center"') &&
    !appSidebarSource.includes("SidebarProjectsList") &&
    !appSidebarSource.includes("SidebarTeamsList") &&
    !appSidebarSource.includes("SidebarFavoritesMenu"),
  "active projects app sidebar should be Agent Center first and not render legacy project sections"
);
assert.ok(
  !sidebarWrapperSource.includes("WorkspaceEditionBadge"),
  "sidebar wrapper should not expose billing or plan upgrade UI"
);
for (const iconName of ["ListChecks", "Bot", "FileText", "Workflow", "HardDrive", "FolderGit2"]) {
  assert.ok(sidebarIconSource.includes(iconName), `${iconName} icon should be mapped for Agent Center sidebar`);
}
assert.ok(
  workspaceSettingsSource.includes('key: "agents"') &&
    workspaceSettingsSource.includes("href: `/settings/agents`") &&
    workspaceSettingsSource.includes('WORKSPACE_SETTINGS["agents"]'),
  "workspace settings should expose an Agent Library navigation item"
);
assert.ok(
  !workspaceSettingsSource.includes('WORKSPACE_SETTINGS["billing-and-plans"],') &&
    !workspaceSettingsSource.includes('WORKSPACE_SETTINGS["export"],'),
  "workspace settings sidebar should not expose billing or export entries"
);
assert.ok(
  !workspaceMembersPageSource.includes("BillingActionsButton"),
  "workspace members page should not expose billing actions"
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
    serviceSource.includes("agent-user-secret-keys") &&
    serviceSource.includes("updateAgent") &&
    serviceSource.includes("updatePrompt"),
  "agent platform service should cover workspace agent resources"
);
assert.ok(
  serviceSource.includes("getProjectSnapshot") &&
    serviceSource.includes("getWorkDirectorySnapshot") &&
    serviceSource.includes("agent-worker-cards") &&
    serviceSource.includes("agent-work-directories") &&
    serviceSource.includes("agent-work-directory-repositories") &&
    serviceSource.includes("agent-worker-mounts") &&
    serviceSource.includes("agent-project-defaults") &&
    serviceSource.includes("agent-task-work-directory-overrides") &&
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
  agentCenterAgentsPageSource.includes("AgentPromptLibraryPage") &&
    agentCenterAgentsPageSource.includes('initialView="agents"') &&
    agentCenterPromptsPageSource.includes("AgentPromptLibraryPage") &&
    agentCenterPromptsPageSource.includes('initialView="prompts"'),
  "Agent Center Agents and Prompts routes should render the real library UI"
);
assert.ok(
  agentCenterLibraryPageSource.includes("getWorkspaceSnapshot") &&
    agentCenterLibraryPageSource.includes("createAgent") &&
    agentCenterLibraryPageSource.includes("updateAgent") &&
    agentCenterLibraryPageSource.includes("createPrompt") &&
    agentCenterLibraryPageSource.includes("updatePrompt") &&
    agentCenterLibraryPageSource.includes("createPromptVersion") &&
    agentCenterLibraryPageSource.includes("createPromptBinding") &&
    agentCenterLibraryPageSource.includes("archive-prompt") &&
    agentCenterLibraryPageSource.includes("prompt_stack"),
  "Agent Center library UI should expose real Agent, Prompt, Prompt Version, and Prompt Stack operations"
);
assert.ok(
  agentCenterWorkersPageSource.includes("WorkerDirectoryPage") &&
    agentCenterWorkersPageSource.includes('initialView="workers"') &&
    agentCenterWorkDirectoriesPageSource.includes("WorkerDirectoryPage") &&
    agentCenterWorkDirectoriesPageSource.includes('initialView="work-directories"'),
  "Agent Center Workers and Work Directories routes should render the real worker directory UI"
);
assert.ok(
  agentCenterWorkerDirectoryPageSource.includes("getWorkDirectorySnapshot") &&
    agentCenterWorkerDirectoryPageSource.includes("createWorkerCard") &&
    agentCenterWorkerDirectoryPageSource.includes("updateWorkerCard") &&
    agentCenterWorkerDirectoryPageSource.includes("createWorkDirectory") &&
    agentCenterWorkerDirectoryPageSource.includes("updateWorkDirectory") &&
    agentCenterWorkerDirectoryPageSource.includes("createRepository") &&
    agentCenterWorkerDirectoryPageSource.includes("createWorkDirectoryRepository") &&
    agentCenterWorkerDirectoryPageSource.includes("createWorkerMount") &&
    !agentCenterWorkerDirectoryPageSource.includes('Mac Studio Worker", "MBP Worker'),
  "Agent Center worker directory UI should expose real Worker, Work Directory, Repository, and Mount operations"
);
assert.ok(
  projectPageSource.includes("createWorkerCard") &&
    projectPageSource.includes("createProjectWorkspace") &&
    projectPageSource.includes("createRepository") &&
    projectPageSource.includes("createProjectDefault") &&
    projectPageSource.includes("updateProjectDefault") &&
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
    agentRunActionSource.includes("selectedWorkDirectory") &&
    agentRunActionSource.includes("createTaskWorkDirectoryOverride") &&
    agentRunActionSource.includes("updateTaskWorkDirectoryOverride") &&
    agentRunActionSource.includes("submitRunIntent") &&
    agentRunActionSource.includes("createRunIntent") &&
    agentRunActionSource.includes("copyRunIntent"),
  "Agent run action should expose a resilient trigger, assemble Agent context, and queue run intents"
);

for (const locale of ["en", "zh-CN", "zh-TW"]) {
  const navigationMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/navigation.json`));
  const workspaceMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/workspace-settings.json`));
  const projectMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/project-settings.json`));
  const workItemMessages = JSON.parse(read(`packages/i18n/src/locales/${locale}/work-item.json`));
  for (const key of ["tasks", "agents", "prompts", "workflows", "workers", "work_directories"]) {
    assert.ok(navigationMessages.sidebar[key], `${locale} sidebar.${key} is required`);
  }
  assert.ok(workspaceMessages.workspace_settings.settings.agents.title, `${locale} workspace agent title is required`);
  assert.ok(
    workspaceMessages.workspace_settings.settings.agents.agent_page_description,
    `${locale} Agent Center agent page description is required`
  );
  assert.ok(
    workspaceMessages.workspace_settings.settings.agents.prompt_page_description,
    `${locale} Agent Center prompt page description is required`
  );
  assert.ok(
    workspaceMessages.workspace_settings.settings.agents.archive_prompt,
    `${locale} Agent Center prompt archive label is required`
  );
  assert.ok(projectMessages.project_settings.agents.label, `${locale} project agent label is required`);
  assert.ok(
    projectMessages.project_settings.agents.work_directories_page_title,
    `${locale} work directories page title is required`
  );
  assert.ok(
    projectMessages.project_settings.agents.create_work_directory,
    `${locale} create work directory label is required`
  );
  assert.ok(projectMessages.project_settings.agents.attach_repository, `${locale} attach repository label is required`);
  assert.ok(projectMessages.project_settings.agents.create_mount, `${locale} create worker mount label is required`);
  assert.ok(
    projectMessages.project_settings.agents.save_project_default,
    `${locale} project default save label is required`
  );
  assert.ok(workItemMessages.issue.agent_run.action, `${locale} work item Agent run action is required`);
  assert.ok(workItemMessages.issue.agent_run.start, `${locale} work item Agent run start is required`);
  assert.ok(workItemMessages.issue.agent_run.queued, `${locale} work item Agent run queued is required`);
}

console.log("agent_platform_settings=passed");

function read(relativePath: string): string {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf-8");
}
