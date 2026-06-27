/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
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
import { useProject } from "@/hooks/store/use-project";
import { useUserPermissions } from "@/hooks/store/user";
// services
import {
  AgentPlatformService,
  type AgentPlatformProjectSnapshot,
  type AgentWorkerCard,
} from "@/services/agent-platform.service";
// local imports
import type { Route } from "./+types/page";
import { AgentsProjectSettingsHeader } from "./header";

const agentPlatformService = new AgentPlatformService();

function AgentsProjectSettingsPage({ params }: Route.ComponentProps) {
  const { workspaceSlug, projectId } = params;
  const { t } = useTranslation();
  const { currentProjectDetails } = useProject();
  const { workspaceUserInfo, allowPermissions } = useUserPermissions();
  const [saving, setSaving] = useState<string | null>(null);

  const canPerformProjectAdminActions = allowPermissions(
    [EUserPermissions.ADMIN],
    EUserPermissionsLevel.PROJECT,
    workspaceSlug,
    projectId
  );
  const { data: snapshot, mutate } = useSWR<AgentPlatformProjectSnapshot>(
    canPerformProjectAdminActions ? `AGENT_PLATFORM_PROJECT_${workspaceSlug}_${projectId}` : null,
    () => agentPlatformService.getProjectSnapshot(workspaceSlug, projectId)
  );

  const pageTitle = currentProjectDetails?.name
    ? `${currentProjectDetails.name} - ${t("project_settings.agents.label")}`
    : undefined;

  if (workspaceUserInfo && !canPerformProjectAdminActions) {
    return <NotAuthorizedView section="settings" isProjectView className="h-auto" />;
  }

  const handleCreateWorkerCard = async (formData: FormData) => {
    await submit("worker", async () => {
      await agentPlatformService.createWorkerCard(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        worker_endpoint: valueOf(formData, "worker_endpoint"),
        capabilities: csvOf(formData, "capabilities"),
      });
    });
  };

  const handleCreateProjectWorkspace = async (formData: FormData) => {
    await submit("workspace", async () => {
      await agentPlatformService.createProjectWorkspace(workspaceSlug, {
        project: projectId,
        worker_card: optionalValueOf(formData, "worker_card"),
        slug: valueOf(formData, "slug"),
        name: valueOf(formData, "name"),
        local_path: valueOf(formData, "local_path"),
        path_policy: valueOf(formData, "path_policy") || "worker_managed",
        meta_git_mode: valueOf(formData, "meta_git_mode") || "local",
        meta_git_remote_url: valueOf(formData, "meta_git_remote_url"),
        status_path: valueOf(formData, "status_path") || "status.md",
        progress_path: valueOf(formData, "progress_path") || "progress.md",
        meta_path: valueOf(formData, "meta_path") || "meta.md",
      });
    });
  };

  const handleCreateRepository = async (formData: FormData) => {
    await submit("repository", async () => {
      await agentPlatformService.createRepository(workspaceSlug, {
        project: projectId,
        key: valueOf(formData, "key"),
        provider: valueOf(formData, "provider") || "github",
        scm_provider: valueOf(formData, "provider") || "github",
        owner: valueOf(formData, "owner"),
        name: valueOf(formData, "name"),
        full_name: valueOf(formData, "full_name") || valueOf(formData, "name"),
        url: valueOf(formData, "url"),
        clone_url: valueOf(formData, "url"),
        default_branch: valueOf(formData, "default_branch") || "default",
        credential_key: valueOf(formData, "credential_key"),
        worktree_strategy: valueOf(formData, "worktree_strategy") || "per_run",
        local_path: valueOf(formData, "local_path"),
        is_required: formData.get("is_required") === "on",
      });
    });
  };

  const handleSaveProjectDefault = async (formData: FormData) => {
    await submit("project-default", async () => {
      const payload = {
        project: projectId,
        work_directory: optionalValueOf(formData, "work_directory"),
        worker_card: optionalValueOf(formData, "worker_card"),
        is_active: true,
      };
      const currentDefault = snapshot?.projectDefaults.find((item) => item.is_active);
      if (currentDefault) {
        await agentPlatformService.updateProjectDefault(workspaceSlug, currentDefault.id, payload);
      } else {
        await agentPlatformService.createProjectDefault(workspaceSlug, payload);
      }
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
        message: t("project_settings.agents.saved"),
      });
    } catch {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: t("common.error"),
        message: t("project_settings.agents.save_failed"),
      });
    } finally {
      setSaving(null);
    }
  };

  return (
    <SettingsContentWrapper header={<AgentsProjectSettingsHeader />} hugging>
      <PageHead title={pageTitle} />
      <div className="flex w-full flex-col gap-8">
        <SettingsHeading
          title={t("project_settings.agents.heading")}
          description={t("project_settings.agents.description")}
        />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-4">
          <Panel title={t("project_settings.agents.worker_cards")}>
            <Form onSubmit={handleCreateWorkerCard}>
              <Field name="key" label={t("project_settings.agents.key")} placeholder="mac-studio" />
              <Field name="name" label={t("common.name")} placeholder="Mac Studio Worker" />
              <Field
                name="worker_endpoint"
                label={t("project_settings.agents.worker_endpoint")}
                placeholder="http://..."
              />
              <Field
                name="capabilities"
                label={t("project_settings.agents.capabilities")}
                placeholder="codex, docker, git"
              />
              <TextArea name="description" label={t("common.description")} rows={3} />
              <SubmitButton disabled={saving === "worker"}>{t("project_settings.agents.create_worker")}</SubmitButton>
            </Form>
            <List
              empty={t("project_settings.agents.no_workers")}
              items={(snapshot?.workerCards ?? []).map((worker) => ({
                id: worker.id,
                title: worker.name,
                meta: worker.key,
                description: worker.worker_endpoint || worker.description,
              }))}
            />
          </Panel>

          <Panel title={t("project_settings.agents.project_workspace")}>
            <Form onSubmit={handleCreateProjectWorkspace}>
              <WorkerSelect workerCards={snapshot?.workerCards ?? []} name="worker_card" optional />
              <Field name="slug" label={t("project_settings.agents.key")} placeholder="token" />
              <Field name="name" label={t("common.name")} placeholder="Token Project Workspace" />
              <Field
                name="local_path"
                label={t("project_settings.agents.local_path")}
                placeholder="/Users/a/agent-worker-workspaces/my-project-meta"
              />
              <Field name="path_policy" label="Path policy" defaultValue="worker_managed" />
              <Field name="meta_git_mode" label="Meta Git mode" defaultValue="local" />
              <Field name="meta_git_remote_url" label="Meta Git remote URL" />
              <Field name="status_path" label="status.md" defaultValue="status.md" />
              <Field name="progress_path" label="progress.md" defaultValue="progress.md" />
              <Field name="meta_path" label="meta.md" defaultValue="meta.md" />
              <SubmitButton disabled={saving === "workspace"}>
                {t("project_settings.agents.create_project_workspace")}
              </SubmitButton>
            </Form>
            <List
              empty={t("project_settings.agents.no_project_workspace")}
              items={(snapshot?.projectWorkspaces ?? []).map((workspace) => ({
                id: workspace.id,
                title: workspace.name || workspace.local_path,
                meta: `${workspace.slug || "-"} · ${workspace.meta_git_mode || "local"}`,
                description: `${workspace.status_path} · ${workspace.progress_path} · ${workspace.meta_path}`,
              }))}
            />
          </Panel>

          <Panel title={t("project_settings.agents.repositories")}>
            <Form onSubmit={handleCreateRepository}>
              <Field name="key" label={t("project_settings.agents.key")} placeholder="agent-control-plane" />
              <Field name="provider" label="Provider" placeholder="github" defaultValue="github" />
              <Field name="owner" label="Owner" placeholder="michaelx1993" />
              <Field name="name" label={t("common.name")} placeholder="michaelx1993/agent-control-plane" />
              <Field name="full_name" label="Full name" placeholder="michaelx1993/agent-control-plane" />
              <Field
                name="url"
                label="Clone URL"
                placeholder="git@github.com:michaelx1993/agent-control-plane.git"
                required
              />
              <Field name="default_branch" label={t("project_settings.agents.default_branch")} defaultValue="default" />
              <Field name="credential_key" label="Credential key" placeholder="github-token" />
              <Field name="worktree_strategy" label="Worktree strategy" defaultValue="per_run" />
              <Field
                name="local_path"
                label={t("project_settings.agents.local_path")}
                placeholder="/Users/a/agent-control-plane"
              />
              <label className="flex items-center gap-2 text-body-sm-regular text-secondary">
                <input name="is_required" type="checkbox" className="size-4" defaultChecked />
                {t("project_settings.agents.required_for_phase_1")}
              </label>
              <SubmitButton disabled={saving === "repository"}>
                {t("project_settings.agents.create_repository")}
              </SubmitButton>
            </Form>
            <List
              empty={t("project_settings.agents.no_repositories")}
              items={(snapshot?.repositories ?? []).map((repo) => ({
                id: repo.id,
                title: repo.full_name || repo.name,
                meta: `${repo.provider} · ${repo.default_branch} · ${repo.worktree_strategy || "per_run"}`,
                description: repo.url,
              }))}
            />
          </Panel>

          <Panel title={t("project_settings.agents.project_default")}>
            <Form onSubmit={handleSaveProjectDefault}>
              <WorkDirectorySelect name="work_directory" optional workDirectories={snapshot?.workDirectories ?? []} />
              <WorkerSelect workerCards={snapshot?.workerCards ?? []} name="worker_card" optional />
              <SubmitButton disabled={saving === "project-default"}>
                {t("project_settings.agents.save_project_default")}
              </SubmitButton>
            </Form>
            <List
              empty={t("project_settings.agents.no_project_default")}
              items={(snapshot?.projectDefaults ?? []).map((projectDefault) => ({
                id: projectDefault.id,
                title: projectDefault.project_identifier || currentProjectDetails?.identifier || projectId,
                meta: `${projectDefault.work_directory_key || "-"} · ${projectDefault.worker_key || "-"}`,
                description: t("project_settings.agents.project_default_description"),
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
        required={props.required ?? (props.name === "key" || props.name === "name" || props.name === "local_path")}
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

function WorkerSelect(props: { name: string; optional?: boolean; workerCards: AgentWorkerCard[] }) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      Worker Card
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        name={props.name}
        required={!props.optional}
      >
        {props.optional && <option value="">-</option>}
        {props.workerCards.map((worker) => (
          <option key={worker.id} value={worker.id}>
            {worker.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function WorkDirectorySelect(props: {
  name: string;
  optional?: boolean;
  workDirectories: Array<{ id: string; name: string }>;
}) {
  return (
    <label className="grid gap-1 text-body-sm-medium text-secondary">
      Work Directory
      <select
        className="focus:border-primary min-h-9 rounded border border-subtle bg-surface-2 px-3 text-body-sm-regular text-primary outline-none"
        name={props.name}
        required={!props.optional}
      >
        {props.optional && <option value="">-</option>}
        {props.workDirectories.map((directory) => (
          <option key={directory.id} value={directory.id}>
            {directory.name}
          </option>
        ))}
      </select>
    </label>
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

export default observer(AgentsProjectSettingsPage);
