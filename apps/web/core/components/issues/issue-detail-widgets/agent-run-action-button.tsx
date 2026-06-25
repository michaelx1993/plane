/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useMemo, useState } from "react";
import { Bot, Copy, ExternalLink } from "lucide-react";
import useSWR from "swr";
// plane imports
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// services
import {
  AgentPlatformService,
  type AgentPlatformProjectSnapshot,
  type AgentPlatformWorkspaceSnapshot,
  type AgentPromptBinding,
  type AgentPromptVersion,
  type AgentUserAgent,
  type AgentWorkerCard,
} from "@/services/agent-platform.service";
type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled: boolean;
};

type PromptStackItem = {
  binding: AgentPromptBinding;
  body: string;
  name: string;
  scope: string;
  version: AgentPromptVersion | null;
};

const agentPlatformService = new AgentPlatformService();
const promptScopeOrder = new Map([
  ["agent", 10],
  ["project", 20],
  ["role", 30],
  ["playbook", 40],
  ["task", 50],
  ["workspace", 60],
]);

export function AgentRunActionButton(props: Props) {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const { t } = useTranslation();
  const [isMounted, setIsMounted] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedRepositoryId, setSelectedRepositoryId] = useState("");
  const [selectedWorkerId, setSelectedWorkerId] = useState("");

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const { data: workspaceSnapshot, isLoading: isWorkspaceLoading } = useSWR<AgentPlatformWorkspaceSnapshot>(
    isMounted ? `AGENT_RUN_WORKSPACE_${workspaceSlug}` : null,
    () => agentPlatformService.getWorkspaceSnapshot(workspaceSlug)
  );
  const { data: projectSnapshot, isLoading: isProjectLoading } = useSWR<AgentPlatformProjectSnapshot>(
    isMounted ? `AGENT_RUN_PROJECT_${workspaceSlug}_${projectId}` : null,
    () => agentPlatformService.getProjectSnapshot(workspaceSlug, projectId)
  );

  const activeAgents = useMemo(
    () => (workspaceSnapshot?.agents ?? []).filter((agent) => agent.is_active),
    [workspaceSnapshot?.agents]
  );
  const activeRepositories = useMemo(
    () => (projectSnapshot?.repositories ?? []).filter((repository) => repository.is_active),
    [projectSnapshot?.repositories]
  );
  const activeWorkers = useMemo(
    () => (projectSnapshot?.workerCards ?? []).filter((worker) => worker.is_active),
    [projectSnapshot?.workerCards]
  );

  const selectedAgent = resolveAgent(activeAgents, selectedAgentId);
  const selectedRepository = resolveById(activeRepositories, selectedRepositoryId);
  const selectedWorker = resolveWorker(projectSnapshot, activeWorkers, selectedWorkerId);
  const promptStack = useMemo(
    () => buildPromptStack(workspaceSnapshot, selectedAgent),
    [selectedAgent, workspaceSnapshot]
  );
  const assembledPrompt = useMemo(
    () =>
      promptStack
        .map((item) => `## ${item.name} (${item.scope}, v${item.version?.version ?? "?"})\n${item.body}`)
        .join("\n\n"),
    [promptStack]
  );
  const availableSecretKeys = useMemo(
    () =>
      (workspaceSnapshot?.secretKeys ?? []).filter((secret) => secret.status === "active").map((secret) => secret.key),
    [workspaceSnapshot?.secretKeys]
  );

  const settingsHref = `/${workspaceSlug}/settings/projects/${projectId}/agents`;
  const isLoading = isWorkspaceLoading || isProjectLoading;
  const runIntent = {
    workItemId: issueId,
    projectId,
    agentId: selectedAgent?.id ?? null,
    repositoryId: selectedRepository?.id ?? null,
    workerId: selectedWorker?.id ?? null,
    targetBranch: selectedRepository?.default_branch || "default",
    promptVersionIds: promptStack.map((item) => item.version?.id).filter(Boolean),
    availableSecretKeys,
  };

  const copyRunIntent = async () => {
    try {
      await copyText(JSON.stringify(runIntent, null, 2));
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: t("common.success"),
        message: t("issue.agent_run.copied"),
      });
    } catch {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: t("common.error"),
        message: t("issue.agent_run.copy_failed"),
      });
    }
  };

  if (!isMounted) return null;

  return (
    <div className="basis-full">
      <div
        aria-disabled={disabled}
        className="inline-flex h-7 w-fit items-center justify-center gap-1 rounded-md border border-strong bg-layer-2 px-2 text-body-xs-medium text-secondary shadow-raised-100"
        data-testid="agent-run-action-trigger"
      >
        <Bot className="h-3.5 w-3.5 flex-shrink-0" strokeWidth={2} />
        <span className="text-body-xs-medium">{t("issue.agent_run.action")}</span>
      </div>

      <div className="mt-2 rounded border border-subtle bg-surface-1 p-4">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-body-sm-medium text-primary">{t("issue.agent_run.title")}</h3>
            <p className="mt-1 text-body-xs-regular text-secondary">
              {t("issue.agent_run.work_item_id")}: {issueId}
            </p>
          </div>
          <a
            className="text-custom-primary-100 inline-flex items-center gap-1 text-body-xs-medium hover:underline"
            href={settingsHref}
          >
            {t("issue.agent_run.project_agents")}
            <ExternalLink className="h-3 w-3" strokeWidth={2} />
          </a>
        </div>

        {isLoading ? (
          <div className="rounded border border-dashed border-subtle p-4 text-body-sm-regular text-tertiary">
            {t("common.loading")}
          </div>
        ) : (
          <div className="grid gap-4">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <SelectField
                label={t("issue.agent_run.agent")}
                onChange={setSelectedAgentId}
                options={activeAgents.map((agent) => ({ label: agent.name, value: agent.id }))}
                value={selectedAgent?.id ?? ""}
              />
              <SelectField
                label={t("issue.agent_run.repository")}
                onChange={setSelectedRepositoryId}
                options={activeRepositories.map((repository) => ({
                  label: repository.full_name || repository.name,
                  value: repository.id,
                }))}
                value={selectedRepository?.id ?? ""}
              />
              <SelectField
                label={t("issue.agent_run.worker")}
                onChange={setSelectedWorkerId}
                options={activeWorkers.map((worker) => ({ label: worker.name, value: worker.id }))}
                value={selectedWorker?.id ?? ""}
              />
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <SummaryCell label={t("issue.agent_run.model")} value={selectedAgent?.model || "-"} />
              <SummaryCell
                label={t("issue.agent_run.target_branch")}
                value={selectedRepository?.default_branch || "default"}
              />
              <SummaryCell
                label={t("issue.agent_run.secret_keys")}
                value={availableSecretKeys.length ? availableSecretKeys.join(", ") : "-"}
              />
            </div>

            <div className="rounded border border-subtle bg-surface-2 p-3">
              <div className="mb-2 text-body-xs-medium text-tertiary uppercase">
                {t("issue.agent_run.prompt_stack")}
              </div>
              {promptStack.length > 0 ? (
                <div className="grid gap-2">
                  {promptStack.map((item) => (
                    <div key={item.binding.id} className="rounded border border-subtle bg-surface-1 p-2">
                      <div className="flex min-w-0 items-center justify-between gap-2">
                        <span className="truncate text-body-xs-medium text-primary">{item.name}</span>
                        <span className="text-caption-regular shrink-0 text-tertiary">
                          {item.scope} · v{item.version?.version ?? "?"}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-body-xs-regular text-secondary">{item.body}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-body-sm-regular text-tertiary">{t("issue.agent_run.no_prompt_stack")}</p>
              )}
            </div>

            <div className="rounded border border-subtle bg-surface-2 p-3">
              <div className="mb-2 text-body-xs-medium text-tertiary uppercase">
                {t("issue.agent_run.assembled_prompt")}
              </div>
              <pre className="max-h-64 overflow-auto rounded bg-surface-1 p-3 text-body-xs-regular break-words whitespace-pre-wrap text-primary">
                {assembledPrompt || t("issue.agent_run.empty_preview")}
              </pre>
            </div>

            <div>
              <Button
                disabled={!selectedAgent || !selectedRepository || !selectedWorker}
                onClick={copyRunIntent}
                size="lg"
                type="button"
              >
                <Copy className="h-3.5 w-3.5" strokeWidth={2} />
                {t("issue.agent_run.copy_intent")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SelectField(props: {
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-body-xs-medium text-secondary">
      {props.label}
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        onChange={(event) => props.onChange(event.currentTarget.value)}
        value={props.value}
      >
        <option value="">-</option>
        {props.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function SummaryCell(props: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded border border-subtle bg-surface-2 p-3">
      <div className="text-caption-regular text-tertiary uppercase">{props.label}</div>
      <div className="mt-1 truncate text-body-sm-medium text-primary">{props.value}</div>
    </div>
  );
}

function resolveAgent(agents: AgentUserAgent[], selectedAgentId: string): AgentUserAgent | undefined {
  return resolveById(agents, selectedAgentId) ?? agents.find((agent) => agent.is_default) ?? agents[0];
}

function resolveWorker(
  snapshot: AgentPlatformProjectSnapshot | undefined,
  workers: AgentWorkerCard[],
  selectedWorkerId: string
): AgentWorkerCard | undefined {
  const selected = resolveById(workers, selectedWorkerId);
  if (selected) return selected;
  const projectWorkspaceWorkerId = snapshot?.projectWorkspaces.find((workspace) => workspace.is_active)?.worker_card;
  return workers.find((worker) => worker.id === projectWorkspaceWorkerId) ?? workers[0];
}

function resolveById<T extends { id: string }>(items: T[], selectedId: string): T | undefined {
  return items.find((item) => item.id === selectedId) ?? items[0];
}

function buildPromptStack(
  snapshot: AgentPlatformWorkspaceSnapshot | undefined,
  selectedAgent: AgentUserAgent | undefined
): PromptStackItem[] {
  if (!snapshot || !selectedAgent) return [];

  const prompts = new Map(snapshot.prompts.map((prompt) => [prompt.id, prompt]));
  const versionsByPrompt = new Map<string, AgentPromptVersion[]>();
  for (const version of snapshot.promptVersions) {
    versionsByPrompt.set(version.prompt, [...(versionsByPrompt.get(version.prompt) ?? []), version]);
  }

  return snapshot.promptBindings
    .filter((binding) => binding.is_active && binding.agent === selectedAgent.id)
    .map((binding) => {
      const prompt = prompts.get(binding.prompt);
      const versions = versionsByPrompt.get(binding.prompt) ?? [];
      const version =
        binding.version_policy === "pinned"
          ? (versions.find((item) => item.id === binding.pinned_version || item.id === binding.prompt_version) ?? null)
          : versions.reduce<AgentPromptVersion | null>(
              (latest, item) => (!latest || item.version > latest.version ? item : latest),
              null
            );

      return {
        binding,
        body: version?.body ?? "",
        name: prompt?.name ?? binding.prompt,
        scope: prompt?.scope ?? binding.slot ?? "agent",
        version,
      };
    })
    .reduce<PromptStackItem[]>((items, item) => {
      const insertAt = items.findIndex((existing) => comparePromptStackItem(item, existing) < 0);
      if (insertAt < 0) {
        items.push(item);
      } else {
        items.splice(insertAt, 0, item);
      }
      return items;
    }, []);
}

function comparePromptStackItem(a: PromptStackItem, b: PromptStackItem): number {
  const scopeDelta = (promptScopeOrder.get(a.scope) ?? 999) - (promptScopeOrder.get(b.scope) ?? 999);
  if (scopeDelta !== 0) return scopeDelta;
  return a.binding.sort_order - b.binding.sort_order;
}

async function copyText(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch {
      // Fall back for HTTP self-hosted deployments where Clipboard API can be blocked.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();

  if (!copied) {
    throw new Error("copy_failed");
  }
}
