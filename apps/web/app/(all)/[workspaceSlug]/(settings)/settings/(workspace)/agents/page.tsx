/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo, useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
// plane imports
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// components
import { NotAuthorizedView } from "@/components/auth-screens/not-authorized-view";
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useUserPermissions } from "@/hooks/store/user";
import { useWorkspace } from "@/hooks/store/use-workspace";
// services
import {
  AgentPlatformService,
  type AgentPlatformWorkspaceSnapshot,
  type AgentPrompt,
  type AgentPromptType,
} from "@/services/agent-platform.service";
// local imports
import type { Route } from "./+types/page";
import { AgentsWorkspaceSettingsHeader } from "./header";

const agentPlatformService = new AgentPlatformService();
const promptTypes: AgentPromptType[] = ["agent", "project", "role", "playbook_task", "business_system"];

function AgentsWorkspaceSettingsPage({ params }: Route.ComponentProps) {
  const { workspaceSlug } = params;
  const { t } = useTranslation();
  const { currentWorkspace } = useWorkspace();
  const { workspaceUserInfo, allowPermissions } = useUserPermissions();
  const [saving, setSaving] = useState<string | null>(null);

  const canPerformWorkspaceAdminActions = allowPermissions([EUserPermissions.ADMIN], EUserPermissionsLevel.WORKSPACE);
  const { data: snapshot, mutate } = useSWR<AgentPlatformWorkspaceSnapshot>(
    canPerformWorkspaceAdminActions ? `AGENT_PLATFORM_WORKSPACE_${workspaceSlug}` : null,
    () => agentPlatformService.getWorkspaceSnapshot(workspaceSlug)
  );

  const promptVersionByPrompt = useMemo(() => {
    const map = new Map<string, number>();
    for (const version of snapshot?.promptVersions ?? []) {
      map.set(version.prompt, Math.max(map.get(version.prompt) ?? 0, version.version));
    }
    return map;
  }, [snapshot?.promptVersions]);

  const pageTitle = currentWorkspace?.name
    ? `${currentWorkspace.name} - ${t("workspace_settings.settings.agents.title")}`
    : undefined;

  if (workspaceUserInfo && !canPerformWorkspaceAdminActions) {
    return <NotAuthorizedView section="settings" className="h-auto" />;
  }

  const handleCreateAgent = async (formData: FormData) => {
    await submit("agent", async () => {
      await agentPlatformService.createAgent(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        runtime: valueOf(formData, "runtime") || "codex",
        model: valueOf(formData, "model"),
        tools: csvOf(formData, "tools"),
        is_default: formData.get("is_default") === "on",
      });
    });
  };

  const handleCreatePrompt = async (formData: FormData) => {
    await submit("prompt", async () => {
      const prompt = await agentPlatformService.createPrompt(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        prompt_type: valueOf(formData, "prompt_type") as AgentPromptType,
        visibility: "workspace",
      });
      await agentPlatformService.createPromptVersion(workspaceSlug, {
        prompt: prompt.id,
        version: 1,
        body: valueOf(formData, "body"),
        variables: csvOf(formData, "variables"),
      });
    });
  };

  const handleCreateRole = async (formData: FormData) => {
    await submit("role", async () => {
      await agentPlatformService.createRole(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        prompt: optionalValueOf(formData, "prompt"),
      });
    });
  };

  const handleCreateBinding = async (formData: FormData) => {
    await submit("binding", async () => {
      await agentPlatformService.createPromptBinding(workspaceSlug, {
        agent: valueOf(formData, "agent"),
        prompt: valueOf(formData, "prompt"),
        prompt_version: optionalValueOf(formData, "prompt_version"),
        role: optionalValueOf(formData, "role"),
        slot: valueOf(formData, "slot") || "agent",
        sort_order: Number(valueOf(formData, "sort_order") || 0),
        is_required: formData.get("is_required") === "on",
      });
    });
  };

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

  return (
    <SettingsContentWrapper header={<AgentsWorkspaceSettingsHeader />} hugging>
      <PageHead title={pageTitle} />
      <div className="flex w-full flex-col gap-8">
        <SettingsHeading
          title={t("workspace_settings.settings.agents.heading")}
          description={t("workspace_settings.settings.agents.description")}
        />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Panel title={t("workspace_settings.settings.agents.agent_library")}>
            <Form onSubmit={handleCreateAgent}>
              <Field name="key" label={t("workspace_settings.settings.agents.key")} placeholder="codex-default" />
              <Field name="name" label={t("common.name")} placeholder="Codex Engineer" />
              <Field name="runtime" label="Runtime" placeholder="codex" defaultValue="codex" />
              <Field name="model" label="Model" placeholder="gpt-5.5" />
              <Field name="tools" label="Tools" placeholder="shell, git, github" />
              <TextArea name="description" label={t("common.description")} rows={3} />
              <label className="flex items-center gap-2 text-body-sm-regular text-secondary">
                <input name="is_default" type="checkbox" className="size-4" />
                {t("workspace_settings.settings.agents.default_agent")}
              </label>
              <SubmitButton disabled={saving === "agent"}>
                {t("workspace_settings.settings.agents.create_agent")}
              </SubmitButton>
            </Form>
            <List
              empty={t("workspace_settings.settings.agents.no_agents")}
              items={(snapshot?.agents ?? []).map((agent) => ({
                id: agent.id,
                title: agent.name,
                meta: `${agent.key} · ${agent.runtime}${agent.model ? ` · ${agent.model}` : ""}`,
                description: agent.description,
              }))}
            />
          </Panel>

          <Panel title={t("workspace_settings.settings.agents.prompt_library")}>
            <Form onSubmit={handleCreatePrompt}>
              <Field name="key" label={t("workspace_settings.settings.agents.key")} placeholder="rd-agent-base" />
              <Field name="name" label={t("common.name")} placeholder="RD Agent Base" />
              <Select
                name="prompt_type"
                label={t("workspace_settings.settings.agents.prompt_type")}
                values={promptTypes}
              />
              <Field name="variables" label="Variables" placeholder="repo, task, status" />
              <TextArea name="description" label={t("common.description")} rows={2} />
              <TextArea name="body" label={t("workspace_settings.settings.agents.prompt_body")} rows={7} required />
              <SubmitButton disabled={saving === "prompt"}>
                {t("workspace_settings.settings.agents.create_prompt")}
              </SubmitButton>
            </Form>
            <List
              empty={t("workspace_settings.settings.agents.no_prompts")}
              items={(snapshot?.prompts ?? []).map((prompt) => ({
                id: prompt.id,
                title: prompt.name,
                meta: `${prompt.key} · ${prompt.prompt_type} · v${promptVersionByPrompt.get(prompt.id) ?? prompt.latest_version}`,
                description: prompt.description,
              }))}
            />
          </Panel>

          <Panel title={t("workspace_settings.settings.agents.roles")}>
            <Form onSubmit={handleCreateRole}>
              <Field name="key" label={t("workspace_settings.settings.agents.key")} placeholder="reviewer" />
              <Field name="name" label={t("common.name")} placeholder="Code Reviewer" />
              <PromptSelect prompts={snapshot?.prompts ?? []} name="prompt" optional />
              <TextArea name="description" label={t("common.description")} rows={3} />
              <SubmitButton disabled={saving === "role"}>
                {t("workspace_settings.settings.agents.create_role")}
              </SubmitButton>
            </Form>
            <List
              empty={t("workspace_settings.settings.agents.no_roles")}
              items={(snapshot?.roles ?? []).map((role) => ({
                id: role.id,
                title: role.name,
                meta: role.key,
                description: role.description,
              }))}
            />
          </Panel>

          <Panel title={t("workspace_settings.settings.agents.prompt_bindings")}>
            <Form onSubmit={handleCreateBinding}>
              <EntitySelect
                name="agent"
                label={t("workspace_settings.settings.agents.agent")}
                values={(snapshot?.agents ?? []).map((agent) => ({ id: agent.id, name: agent.name }))}
              />
              <PromptSelect prompts={snapshot?.prompts ?? []} name="prompt" />
              <EntitySelect
                name="prompt_version"
                label={t("workspace_settings.settings.agents.prompt_version")}
                optional
                values={(snapshot?.promptVersions ?? []).map((version) => ({
                  id: version.id,
                  name: `v${version.version}`,
                }))}
              />
              <EntitySelect
                name="role"
                label={t("common.role")}
                optional
                values={(snapshot?.roles ?? []).map((role) => ({ id: role.id, name: role.name }))}
              />
              <Field name="slot" label="Slot" placeholder="agent" defaultValue="agent" />
              <Field
                name="sort_order"
                label={t("workspace_settings.settings.agents.order")}
                placeholder="0"
                type="number"
              />
              <label className="flex items-center gap-2 text-body-sm-regular text-secondary">
                <input name="is_required" type="checkbox" className="size-4" defaultChecked />
                {t("workspace_settings.settings.agents.required")}
              </label>
              <SubmitButton disabled={saving === "binding"}>
                {t("workspace_settings.settings.agents.create_binding")}
              </SubmitButton>
            </Form>
            <List
              empty={t("workspace_settings.settings.agents.no_bindings")}
              items={(snapshot?.promptBindings ?? []).map((binding) => ({
                id: binding.id,
                title: `${nameFor(snapshot?.agents, binding.agent)} -> ${nameFor(snapshot?.prompts, binding.prompt)}`,
                meta: `${binding.slot} · #${binding.sort_order}`,
                description: binding.role ? `${t("common.role")}: ${nameFor(snapshot?.roles, binding.role)}` : "",
              }))}
            />
          </Panel>
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

function Form(props: { children: React.ReactNode; onSubmit: (formData: FormData) => Promise<void> }) {
  const { children, onSubmit } = props;

  return (
    <form
      className="mb-5 grid grid-cols-1 gap-3 rounded border border-subtle bg-surface-1 p-4"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(new FormData(event.currentTarget));
        event.currentTarget.reset();
      }}
    >
      {children}
    </form>
  );
}

function Panel(props: { children: React.ReactNode; title: string }) {
  return (
    <section className="min-w-0">
      <h3 className="mb-3 text-h5-medium text-primary">{props.title}</h3>
      {props.children}
    </section>
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

function TextArea(props: { label: string; name: string; required?: boolean; rows: number }) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <textarea
        className="focus:border-primary rounded border border-subtle bg-surface-2 px-3 py-2 text-body-sm-regular text-primary outline-none"
        name={props.name}
        required={props.required}
        rows={props.rows}
      />
    </label>
  );
}

function Select(props: { label: string; name: string; values: string[] }) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      {props.label}
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
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

function PromptSelect(props: { name: string; optional?: boolean; prompts: AgentPrompt[] }) {
  return (
    <EntitySelect
      label="Prompt"
      name={props.name}
      optional={props.optional}
      values={props.prompts.map((prompt) => ({ id: prompt.id, name: prompt.name }))}
    />
  );
}

function SubmitButton(props: { children: React.ReactNode; disabled?: boolean }) {
  return (
    <div>
      <Button disabled={props.disabled} size="lg" type="submit" variant="primary">
        {props.children}
      </Button>
    </div>
  );
}

function List(props: {
  empty: string;
  items: Array<{ description?: string; id: string; meta: string; title: string }>;
}) {
  if (props.items.length === 0) {
    return (
      <div className="rounded border border-dashed border-subtle p-4 text-body-sm-regular text-tertiary">
        {props.empty}
      </div>
    );
  }

  return (
    <div className="grid gap-2">
      {props.items.map((item) => (
        <div key={item.id} className="rounded border border-subtle bg-surface-1 p-3">
          <div className="flex min-w-0 items-center justify-between gap-3">
            <div className="min-w-0 truncate text-body-sm-medium text-primary">{item.title}</div>
            <div className="text-caption-regular shrink-0 text-tertiary">{item.meta}</div>
          </div>
          {item.description && (
            <p className="mt-1 line-clamp-2 text-body-xs-regular text-secondary">{item.description}</p>
          )}
        </div>
      ))}
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

function nameFor(items: Array<{ id: string; name: string }> | undefined, id: string): string {
  return items?.find((item) => item.id === id)?.name ?? id;
}

export default observer(AgentsWorkspaceSettingsPage);
