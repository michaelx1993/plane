/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo, useState } from "react";
import { Archive, Bot, FileText, Link2, Pencil, Plus, RefreshCw } from "lucide-react";
import useSWR from "swr";
// plane imports
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// components
import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";
// services
import {
  AgentPlatformService,
  type AgentPlatformWorkspaceSnapshot,
  type AgentPromptKind,
  type AgentPromptScope,
  type AgentPromptVersionPolicy,
  type AgentUserAgent,
} from "@/services/agent-platform.service";

type TAgentPromptLibraryPageProps = {
  initialView: "agents" | "prompts";
  workspaceSlug: string;
};

const agentPlatformService = new AgentPlatformService();
const promptScopes: AgentPromptScope[] = ["agent", "project", "role", "playbook", "task", "workspace"];
const promptKinds: AgentPromptKind[] = [
  "instruction",
  "context",
  "constraint",
  "workflow",
  "style",
  "safety",
  "output_contract",
];
const versionPolicies: AgentPromptVersionPolicy[] = ["latest", "pinned"];
const emptyAgents: AgentPlatformWorkspaceSnapshot["agents"] = [];
const emptyPrompts: AgentPlatformWorkspaceSnapshot["prompts"] = [];
const emptyPromptVersions: AgentPlatformWorkspaceSnapshot["promptVersions"] = [];
const emptyPromptBindings: AgentPlatformWorkspaceSnapshot["promptBindings"] = [];
const emptyRoles: AgentPlatformWorkspaceSnapshot["roles"] = [];

export function AgentPromptLibraryPage(props: TAgentPromptLibraryPageProps) {
  const { initialView, workspaceSlug } = props;
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState(initialView);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  const {
    data: snapshot,
    isLoading,
    mutate,
  } = useSWR<AgentPlatformWorkspaceSnapshot>(`AGENT_CONTROL_CENTER_LIBRARY_${workspaceSlug}`, () =>
    agentPlatformService.getWorkspaceSnapshot(workspaceSlug)
  );

  const agents = snapshot?.agents ?? emptyAgents;
  const prompts = snapshot?.prompts ?? emptyPrompts;
  const promptVersions = snapshot?.promptVersions ?? emptyPromptVersions;
  const bindings = snapshot?.promptBindings ?? emptyPromptBindings;
  const roles = snapshot?.roles ?? emptyRoles;
  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? agents[0];
  const selectedPrompt = prompts.find((prompt) => prompt.id === selectedPromptId) ?? prompts[0];
  const promptVersionByPrompt = useMemo(() => {
    const map = new Map<string, number>();
    for (const version of promptVersions)
      map.set(version.prompt, Math.max(map.get(version.prompt) ?? 0, version.version));
    return map;
  }, [promptVersions]);
  const promptVersionsForSelectedPrompt = promptVersions.filter((version) => version.prompt === selectedPrompt?.id);

  const title = activeView === "agents" ? t("navigation.sidebar.agents") : t("navigation.sidebar.prompts");
  const subtitle =
    activeView === "agents"
      ? t("workspace_settings.settings.agents.agent_page_description")
      : t("workspace_settings.settings.agents.prompt_page_description");

  const submit = async (key: string, action: () => Promise<void>) => {
    setSaving(key);
    try {
      await action();
      await mutate();
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: t("common.success"),
        message: t("workspace_settings.settings.agents.saved"),
      });
    } catch {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: t("common.error"),
        message: t("workspace_settings.settings.agents.save_failed"),
      });
    } finally {
      setSaving(null);
    }
  };

  const handleCreateAgent = async (formData: FormData) => {
    await submit("create-agent", async () => {
      const agent = await agentPlatformService.createAgent(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        runtime: valueOf(formData, "runtime") || "codex",
        model: valueOf(formData, "model"),
        tools: csvOf(formData, "tools"),
        is_default: formData.get("is_default") === "on",
      });
      setSelectedAgentId(agent.id);
    });
  };

  const handleUpdateAgent = async (formData: FormData) => {
    if (!selectedAgent) return;
    await submit("update-agent", async () => {
      await agentPlatformService.updateAgent(workspaceSlug, selectedAgent.id, {
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        runtime: valueOf(formData, "runtime") || "codex",
        model: valueOf(formData, "model"),
        tools: csvOf(formData, "tools"),
        is_default: formData.get("is_default") === "on",
        is_active: formData.get("is_active") === "on",
      });
    });
  };

  const handleCreatePrompt = async (formData: FormData) => {
    await submit("create-prompt", async () => {
      const prompt = await agentPlatformService.createPrompt(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        scope: valueOf(formData, "scope") as AgentPromptScope,
        kind: valueOf(formData, "kind") as AgentPromptKind,
        visibility: "workspace",
        status: valueOf(formData, "status") || "active",
        is_active: true,
      });
      await agentPlatformService.createPromptVersion(workspaceSlug, {
        prompt: prompt.id,
        body: valueOf(formData, "body"),
        variables: csvOf(formData, "variables"),
        changelog: valueOf(formData, "changelog"),
      });
      setSelectedPromptId(prompt.id);
    });
  };

  const handleUpdatePrompt = async (formData: FormData) => {
    if (!selectedPrompt) return;
    await submit("update-prompt", async () => {
      await agentPlatformService.updatePrompt(workspaceSlug, selectedPrompt.id, {
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        scope: valueOf(formData, "scope") as AgentPromptScope,
        kind: valueOf(formData, "kind") as AgentPromptKind,
        status: valueOf(formData, "status"),
        is_active: formData.get("is_active") === "on",
      });
    });
  };

  const handleCreatePromptVersion = async (formData: FormData) => {
    if (!selectedPrompt) return;
    await submit("create-version", async () => {
      await agentPlatformService.createPromptVersion(workspaceSlug, {
        prompt: selectedPrompt.id,
        body: valueOf(formData, "body"),
        variables: csvOf(formData, "variables"),
        changelog: valueOf(formData, "changelog"),
      });
    });
  };

  const handleArchivePrompt = async () => {
    if (!selectedPrompt) return;
    await submit("archive-prompt", async () => {
      await agentPlatformService.updatePrompt(workspaceSlug, selectedPrompt.id, {
        status: "archived",
        is_active: false,
      });
    });
  };

  const handleCreateBinding = async (formData: FormData) => {
    await submit("create-binding", async () => {
      const promptVersion = optionalValueOf(formData, "prompt_version");
      await agentPlatformService.createPromptBinding(workspaceSlug, {
        agent: valueOf(formData, "agent"),
        prompt: valueOf(formData, "prompt"),
        prompt_version: promptVersion,
        pinned_version: promptVersion,
        target_type: "user_agent",
        version_policy: valueOf(formData, "version_policy") as AgentPromptVersionPolicy,
        role: optionalValueOf(formData, "role"),
        slot: valueOf(formData, "slot") || "agent",
        sort_order: Number(valueOf(formData, "sort_order") || 0),
        is_required: formData.get("is_required") === "on",
      });
    });
  };

  return (
    <>
      <AppHeader
        header={
          <div className="flex items-center justify-between gap-3 px-5 py-3">
            <div className="flex min-w-0 items-center gap-2">
              {activeView === "agents" ? (
                <Bot className="size-4 shrink-0 text-secondary" />
              ) : (
                <FileText className="size-4 shrink-0 text-secondary" />
              )}
              <div className="min-w-0">
                <h1 className="text-lg truncate font-semibold text-primary">{title}</h1>
                <p className="text-xs truncate text-secondary">{subtitle}</p>
              </div>
            </div>
            <Button
              aria-label={t("workspace_settings.settings.agents.refresh")}
              disabled={isLoading}
              onClick={() => void mutate()}
              prependIcon={<RefreshCw className="size-3.5" />}
              size="sm"
              variant="secondary"
            >
              {t("workspace_settings.settings.agents.refresh")}
            </Button>
          </div>
        }
      />
      <ContentWrapper>
        <PageHead title={title} />
        <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex rounded border border-subtle bg-surface-1 p-1">
              <SegmentButton active={activeView === "agents"} onClick={() => setActiveView("agents")}>
                <Bot className="size-3.5" />
                {t("workspace_settings.settings.agents.agent_library")}
              </SegmentButton>
              <SegmentButton active={activeView === "prompts"} onClick={() => setActiveView("prompts")}>
                <FileText className="size-3.5" />
                {t("workspace_settings.settings.agents.prompt_library")}
              </SegmentButton>
            </div>
            <div className="flex gap-2 text-body-sm-regular text-secondary">
              <Metric label={t("workspace_settings.settings.agents.agent_library")} value={agents.length} />
              <Metric label={t("workspace_settings.settings.agents.prompt_library")} value={prompts.length} />
              <Metric label={t("workspace_settings.settings.agents.prompt_bindings")} value={bindings.length} />
            </div>
          </div>

          {activeView === "agents" ? (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.35fr)]">
              <section className="min-w-0">
                <SectionHeader
                  icon={<Plus className="size-4" />}
                  title={t("workspace_settings.settings.agents.create_agent")}
                  description={t("workspace_settings.settings.agents.create_agent_description")}
                />
                <Form onSubmit={handleCreateAgent}>
                  <Field name="key" label={t("workspace_settings.settings.agents.key")} placeholder="codex-default" />
                  <Field name="name" label={t("common.name")} placeholder="Codex Engineer" />
                  <div className="grid gap-3 md:grid-cols-2">
                    <Field name="runtime" label="Runtime" placeholder="codex" defaultValue="codex" />
                    <Field name="model" label="Model" placeholder="gpt-5.5" />
                  </div>
                  <Field name="tools" label="Tools" placeholder="shell, git, github" />
                  <TextArea name="description" label={t("common.description")} rows={3} />
                  <Checkbox name="is_default" label={t("workspace_settings.settings.agents.default_agent")} />
                  <SubmitButton
                    disabled={saving === "create-agent"}
                    icon={<Plus className="size-3.5" />}
                    label={t("workspace_settings.settings.agents.create_agent")}
                  />
                </Form>
              </section>

              <section className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <LibraryList
                  empty={t("workspace_settings.settings.agents.no_agents")}
                  items={agents.map((agent) => ({
                    id: agent.id,
                    title: agent.name,
                    description: agent.description,
                    meta: `${agent.key} · ${agent.runtime}${agent.model ? ` · ${agent.model}` : ""}`,
                    active: agent.id === selectedAgent?.id,
                    status: agent.is_active ? "active" : "archived",
                  }))}
                  onSelect={(id) => setSelectedAgentId(id)}
                  title={t("workspace_settings.settings.agents.my_agents")}
                />

                <div className="min-w-0">
                  <SectionHeader
                    icon={<Pencil className="size-4" />}
                    title={selectedAgent?.name ?? t("workspace_settings.settings.agents.agent_detail")}
                    description={t("workspace_settings.settings.agents.agent_detail_description")}
                  />
                  {selectedAgent ? (
                    <div className="grid gap-4">
                      <Form key={selectedAgent.id} onSubmit={handleUpdateAgent}>
                        <Field name="name" label={t("common.name")} defaultValue={selectedAgent.name} />
                        <div className="grid gap-3 md:grid-cols-2">
                          <Field name="runtime" label="Runtime" defaultValue={selectedAgent.runtime} />
                          <Field name="model" label="Model" defaultValue={selectedAgent.model} />
                        </div>
                        <Field name="tools" label="Tools" defaultValue={(selectedAgent.tools ?? []).join(", ")} />
                        <TextArea
                          name="description"
                          label={t("common.description")}
                          rows={3}
                          defaultValue={selectedAgent.description}
                        />
                        <div className="grid gap-2 md:grid-cols-2">
                          <Checkbox
                            name="is_default"
                            label={t("workspace_settings.settings.agents.default_agent")}
                            defaultChecked={selectedAgent.is_default}
                          />
                          <Checkbox
                            name="is_active"
                            label={t("workspace_settings.settings.agents.active")}
                            defaultChecked={selectedAgent.is_active}
                          />
                        </div>
                        <SubmitButton
                          disabled={saving === "update-agent"}
                          icon={<Pencil className="size-3.5" />}
                          label={t("workspace_settings.settings.agents.update_agent")}
                        />
                      </Form>
                      <PromptStack agent={selectedAgent} empty={t("workspace_settings.settings.agents.no_bindings")} />
                    </div>
                  ) : (
                    <EmptyState message={t("workspace_settings.settings.agents.no_agents")} />
                  )}
                </div>
              </section>

              <section className="xl:col-span-2">
                <SectionHeader
                  icon={<Link2 className="size-4" />}
                  title={t("workspace_settings.settings.agents.prompt_stack")}
                  description={t("workspace_settings.settings.agents.prompt_stack_description")}
                />
                <Form onSubmit={handleCreateBinding}>
                  <div className="grid gap-3 lg:grid-cols-4">
                    <EntitySelect
                      name="agent"
                      label={t("workspace_settings.settings.agents.agent")}
                      values={agents.map((agent) => ({ id: agent.id, name: agent.name }))}
                    />
                    <EntitySelect
                      name="prompt"
                      label="Prompt"
                      values={prompts.map((prompt) => ({ id: prompt.id, name: prompt.name }))}
                    />
                    <EntitySelect
                      name="prompt_version"
                      label={t("workspace_settings.settings.agents.prompt_version")}
                      optional
                      values={promptVersions.map((version) => ({
                        id: version.id,
                        name: `${nameFor(prompts, version.prompt)} · v${version.version}`,
                      }))}
                    />
                    <Select
                      name="version_policy"
                      label={t("workspace_settings.settings.agents.version_policy")}
                      values={versionPolicies}
                    />
                  </div>
                  <div className="grid gap-3 lg:grid-cols-4">
                    <EntitySelect
                      name="role"
                      label={t("common.role")}
                      optional
                      values={roles.map((role) => ({ id: role.id, name: role.name }))}
                    />
                    <Field name="slot" label="Slot" placeholder="agent" defaultValue="agent" />
                    <Field
                      name="sort_order"
                      label={t("workspace_settings.settings.agents.order")}
                      placeholder="0"
                      type="number"
                    />
                    <Checkbox
                      name="is_required"
                      label={t("workspace_settings.settings.agents.required")}
                      defaultChecked
                    />
                  </div>
                  <SubmitButton
                    disabled={saving === "create-binding"}
                    icon={<Link2 className="size-3.5" />}
                    label={t("workspace_settings.settings.agents.create_binding")}
                  />
                </Form>
              </section>
            </div>
          ) : (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.35fr)]">
              <section className="min-w-0">
                <SectionHeader
                  icon={<Plus className="size-4" />}
                  title={t("workspace_settings.settings.agents.create_prompt")}
                  description={t("workspace_settings.settings.agents.create_prompt_description")}
                />
                <Form onSubmit={handleCreatePrompt}>
                  <Field name="key" label={t("workspace_settings.settings.agents.key")} placeholder="rd-agent-base" />
                  <Field name="name" label={t("common.name")} placeholder="RD Agent Base" />
                  <div className="grid gap-3 md:grid-cols-2">
                    <Select
                      name="scope"
                      label={t("workspace_settings.settings.agents.prompt_scope")}
                      values={promptScopes}
                    />
                    <Select
                      name="kind"
                      label={t("workspace_settings.settings.agents.prompt_kind")}
                      values={promptKinds}
                    />
                  </div>
                  <Field name="variables" label="Variables" placeholder="repo, task, status" />
                  <TextArea name="description" label={t("common.description")} rows={2} />
                  <TextArea name="body" label={t("workspace_settings.settings.agents.prompt_body")} rows={9} required />
                  <Field name="changelog" label={t("workspace_settings.settings.agents.changelog")} />
                  <input name="status" type="hidden" value="active" />
                  <SubmitButton
                    disabled={saving === "create-prompt"}
                    icon={<Plus className="size-3.5" />}
                    label={t("workspace_settings.settings.agents.create_prompt")}
                  />
                </Form>
              </section>

              <section className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <LibraryList
                  empty={t("workspace_settings.settings.agents.no_prompts")}
                  items={prompts.map((prompt) => ({
                    id: prompt.id,
                    title: prompt.name,
                    description: prompt.description,
                    meta: `${prompt.key} · ${prompt.scope ?? prompt.prompt_type} · ${prompt.kind} · v${promptVersionByPrompt.get(prompt.id) ?? prompt.latest_version}`,
                    active: prompt.id === selectedPrompt?.id,
                    status: prompt.status,
                  }))}
                  onSelect={(id) => setSelectedPromptId(id)}
                  title={t("workspace_settings.settings.agents.prompt_library")}
                />

                <div className="min-w-0">
                  <SectionHeader
                    icon={<Pencil className="size-4" />}
                    title={selectedPrompt?.name ?? t("workspace_settings.settings.agents.prompt_detail")}
                    description={t("workspace_settings.settings.agents.prompt_detail_description")}
                  />
                  {selectedPrompt ? (
                    <div className="grid gap-4">
                      <Form key={selectedPrompt.id} onSubmit={handleUpdatePrompt}>
                        <Field name="name" label={t("common.name")} defaultValue={selectedPrompt.name} />
                        <div className="grid gap-3 md:grid-cols-2">
                          <Select
                            name="scope"
                            label={t("workspace_settings.settings.agents.prompt_scope")}
                            values={promptScopes}
                            defaultValue={selectedPrompt.scope}
                          />
                          <Select
                            name="kind"
                            label={t("workspace_settings.settings.agents.prompt_kind")}
                            values={promptKinds}
                            defaultValue={selectedPrompt.kind}
                          />
                        </div>
                        <Select
                          name="status"
                          label={t("workspace_settings.settings.agents.status")}
                          values={["draft", "active", "archived"]}
                          defaultValue={selectedPrompt.status}
                        />
                        <TextArea
                          name="description"
                          label={t("common.description")}
                          rows={3}
                          defaultValue={selectedPrompt.description}
                        />
                        <Checkbox
                          name="is_active"
                          label={t("workspace_settings.settings.agents.active")}
                          defaultChecked={selectedPrompt.is_active}
                        />
                        <div className="flex flex-wrap gap-2">
                          <Button
                            disabled={saving === "update-prompt"}
                            prependIcon={<Pencil className="size-3.5" />}
                            size="lg"
                            type="submit"
                            variant="primary"
                          >
                            {t("workspace_settings.settings.agents.update_prompt")}
                          </Button>
                          <Button
                            disabled={saving === "archive-prompt" || selectedPrompt.status === "archived"}
                            onClick={() => void handleArchivePrompt()}
                            prependIcon={<Archive className="size-3.5" />}
                            size="lg"
                            type="button"
                            variant="secondary"
                          >
                            {t("workspace_settings.settings.agents.archive_prompt")}
                          </Button>
                        </div>
                      </Form>
                      <section>
                        <SectionHeader
                          icon={<FileText className="size-4" />}
                          title={t("workspace_settings.settings.agents.version_history")}
                          description={t("workspace_settings.settings.agents.version_history_description")}
                        />
                        <div className="grid gap-2">
                          {promptVersionsForSelectedPrompt.length === 0 ? (
                            <EmptyState message={t("workspace_settings.settings.agents.no_versions")} />
                          ) : (
                            promptVersionsForSelectedPrompt
                              .slice()
                              .toSorted((a, b) => b.version - a.version)
                              .map((version) => (
                                <div key={version.id} className="rounded border border-subtle bg-surface-1 p-3">
                                  <div className="flex items-center justify-between gap-3">
                                    <div className="text-body-sm-medium text-primary">v{version.version}</div>
                                    <div className="text-caption-regular text-tertiary">
                                      {version.variables?.join(", ") || "variables: -"}
                                    </div>
                                  </div>
                                  {version.changelog && (
                                    <p className="mt-1 text-body-xs-regular text-secondary">{version.changelog}</p>
                                  )}
                                  <pre className="mt-2 max-h-36 overflow-auto rounded bg-surface-2 p-2 text-body-xs-regular whitespace-pre-wrap text-secondary">
                                    {version.body}
                                  </pre>
                                </div>
                              ))
                          )}
                        </div>
                      </section>
                      <Form onSubmit={handleCreatePromptVersion}>
                        <TextArea
                          name="body"
                          label={t("workspace_settings.settings.agents.prompt_body")}
                          rows={8}
                          required
                        />
                        <Field name="variables" label="Variables" placeholder="repo, task, status" />
                        <Field name="changelog" label={t("workspace_settings.settings.agents.changelog")} />
                        <SubmitButton
                          disabled={saving === "create-version"}
                          icon={<Plus className="size-3.5" />}
                          label={t("workspace_settings.settings.agents.create_prompt_version")}
                        />
                      </Form>
                    </div>
                  ) : (
                    <EmptyState message={t("workspace_settings.settings.agents.no_prompts")} />
                  )}
                </div>
              </section>
            </div>
          )}
        </main>
      </ContentWrapper>
    </>
  );
}

function SegmentButton(props: { active: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      className={`flex min-h-8 items-center gap-2 rounded px-3 text-body-sm-medium ${
        props.active ? "shadow-sm bg-surface-2 text-primary" : "text-secondary hover:text-primary"
      }`}
      onClick={props.onClick}
      type="button"
    >
      {props.children}
    </button>
  );
}

function Metric(props: { label: string; value: number }) {
  return (
    <div className="rounded border border-subtle bg-surface-1 px-3 py-2">
      <div className="text-caption-regular text-tertiary">{props.label}</div>
      <div className="text-base font-semibold text-primary">{props.value}</div>
    </div>
  );
}

function SectionHeader(props: { description?: string; icon: React.ReactNode; title: string }) {
  return (
    <div className="mb-3 flex items-start gap-2">
      <div className="mt-0.5 text-secondary">{props.icon}</div>
      <div className="min-w-0">
        <h2 className="text-h5-medium text-primary">{props.title}</h2>
        {props.description && <p className="mt-1 text-body-sm-regular text-secondary">{props.description}</p>}
      </div>
    </div>
  );
}

function Form(props: { children: React.ReactNode; onSubmit: (formData: FormData) => Promise<void> }) {
  const { children, onSubmit } = props;

  return (
    <form
      className="grid grid-cols-1 gap-3 rounded border border-subtle bg-surface-1 p-4"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(new FormData(event.currentTarget));
      }}
    >
      {children}
    </form>
  );
}

function Field(props: {
  defaultValue?: string;
  label: string;
  name: string;
  placeholder?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <input
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        defaultValue={props.defaultValue}
        name={props.name}
        placeholder={props.placeholder}
        required={props.required ?? (props.name === "key" || props.name === "name")}
        type={props.type ?? "text"}
      />
    </label>
  );
}

function TextArea(props: { defaultValue?: string; label: string; name: string; required?: boolean; rows: number }) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <textarea
        className="focus:border-primary rounded border border-subtle bg-surface-2 px-3 py-2 text-body-sm-regular text-primary outline-none"
        defaultValue={props.defaultValue}
        name={props.name}
        required={props.required}
        rows={props.rows}
      />
    </label>
  );
}

function Select(props: { defaultValue?: string; label: string; name: string; values: string[] }) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        defaultValue={props.defaultValue}
        name={props.name}
      >
        {props.values.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>
    </label>
  );
}

function EntitySelect(props: {
  label: string;
  name: string;
  optional?: boolean;
  values: Array<{ id: string; name: string }>;
}) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        name={props.name}
        required={!props.optional}
      >
        {props.optional && <option value="">-</option>}
        {props.values.map((value) => (
          <option key={value.id} value={value.id}>
            {value.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function Checkbox(props: { defaultChecked?: boolean; label: string; name: string }) {
  return (
    <label className="flex min-h-9 items-center gap-2 text-body-sm-regular text-secondary">
      <input className="size-4" defaultChecked={props.defaultChecked} name={props.name} type="checkbox" />
      {props.label}
    </label>
  );
}

function SubmitButton(props: { disabled?: boolean; icon: React.ReactElement; label: string }) {
  return (
    <div>
      <Button disabled={props.disabled} prependIcon={props.icon} size="lg" type="submit" variant="primary">
        {props.label}
      </Button>
    </div>
  );
}

function LibraryList(props: {
  empty: string;
  items: Array<{ active: boolean; description?: string; id: string; meta: string; status: string; title: string }>;
  onSelect: (id: string) => void;
  title: string;
}) {
  return (
    <div className="min-w-0">
      <SectionHeader icon={<FileText className="size-4" />} title={props.title} />
      {props.items.length === 0 ? (
        <EmptyState message={props.empty} />
      ) : (
        <div className="grid gap-2">
          {props.items.map((item) => (
            <button
              key={item.id}
              className={`rounded border p-3 text-left ${
                item.active ? "border-primary-300 bg-surface-2" : "border-subtle bg-surface-1 hover:bg-surface-2"
              }`}
              onClick={() => props.onSelect(item.id)}
              type="button"
            >
              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="min-w-0 truncate text-body-sm-medium text-primary">{item.title}</div>
                <span className="text-caption-regular rounded bg-surface-2 px-2 py-0.5 text-tertiary">
                  {item.status}
                </span>
              </div>
              <div className="text-caption-regular mt-1 truncate text-tertiary">{item.meta}</div>
              {item.description && (
                <p className="mt-2 line-clamp-2 text-body-xs-regular text-secondary">{item.description}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function PromptStack(props: { agent: AgentUserAgent; empty: string }) {
  const stack = props.agent.prompt_stack ?? [];
  if (stack.length === 0) return <EmptyState message={props.empty} />;

  return (
    <section>
      <SectionHeader icon={<Link2 className="size-4" />} title="Prompt stack" />
      <div className="grid gap-2">
        {stack
          .slice()
          .toSorted((a, b) => a.sort_order - b.sort_order)
          .map((item) => (
            <div key={item.id} className="rounded border border-subtle bg-surface-1 p-3">
              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="min-w-0 truncate text-body-sm-medium text-primary">{item.prompt_name}</div>
                <div className="text-caption-regular shrink-0 text-tertiary">v{item.resolved_version}</div>
              </div>
              <div className="text-caption-regular mt-1 text-tertiary">
                {item.slot} · {item.prompt_scope} · {item.prompt_kind} · {item.version_policy}
              </div>
              {item.role_key && <div className="mt-1 text-body-xs-regular text-secondary">{item.role_key}</div>}
            </div>
          ))}
      </div>
    </section>
  );
}

function EmptyState(props: { message: string }) {
  return (
    <div className="rounded border border-dashed border-subtle p-4 text-body-sm-regular text-tertiary">
      {props.message}
    </div>
  );
}

function valueOf(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

function optionalValueOf(formData: FormData, key: string): string | null {
  const value = valueOf(formData, key);
  return value.length > 0 ? value : null;
}

function csvOf(formData: FormData, key: string): string[] {
  return valueOf(formData, key)
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

function nameFor(items: Array<{ id: string; name: string }>, id: string): string {
  return items.find((item) => item.id === id)?.name ?? id;
}
