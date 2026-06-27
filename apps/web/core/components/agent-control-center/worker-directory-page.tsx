/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo, useState } from "react";
import { FolderGit2, GitBranch, HardDrive, Link2, Pencil, Plus, RefreshCw, Server } from "lucide-react";
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
  type AgentPlatformWorkDirectorySnapshot,
  type AgentRepository,
  type AgentWorkDirectory,
  type AgentWorkDirectoryRepository,
  type AgentWorkerCard,
  type AgentWorkerMount,
} from "@/services/agent-platform.service";

type TWorkerDirectoryPageProps = {
  initialView: "workers" | "work-directories";
  workspaceSlug: string;
};

const agentPlatformService = new AgentPlatformService();
const emptyWorkers: AgentWorkerCard[] = [];
const emptyWorkDirectories: AgentWorkDirectory[] = [];
const emptyRepositories: AgentRepository[] = [];
const emptyDirectoryRepositories: AgentWorkDirectoryRepository[] = [];
const emptyWorkerMounts: AgentWorkerMount[] = [];

export function WorkerDirectoryPage(props: TWorkerDirectoryPageProps) {
  const { initialView, workspaceSlug } = props;
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState(initialView);
  const [selectedWorkDirectoryId, setSelectedWorkDirectoryId] = useState<string | null>(null);
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  const {
    data: snapshot,
    isLoading,
    mutate,
  } = useSWR<AgentPlatformWorkDirectorySnapshot>(`AGENT_CONTROL_CENTER_WORK_DIRECTORIES_${workspaceSlug}`, () =>
    agentPlatformService.getWorkDirectorySnapshot(workspaceSlug)
  );

  const workers = snapshot?.workerCards ?? emptyWorkers;
  const workDirectories = snapshot?.workDirectories ?? emptyWorkDirectories;
  const repositories = snapshot?.repositories ?? emptyRepositories;
  const directoryRepositories = snapshot?.workDirectoryRepositories ?? emptyDirectoryRepositories;
  const workerMounts = snapshot?.workerMounts ?? emptyWorkerMounts;
  const activeWorkers = workers.filter((worker) => worker.is_active);
  const activeWorkDirectories = workDirectories.filter((directory) => directory.is_active);
  const activeRepositories = repositories.filter((repository) => repository.is_active);
  const selectedWorkDirectory =
    activeWorkDirectories.find((directory) => directory.id === selectedWorkDirectoryId) ?? activeWorkDirectories[0];
  const selectedWorker = activeWorkers.find((worker) => worker.id === selectedWorkerId) ?? activeWorkers[0];
  const selectedDirectoryRepositories = useMemo(
    () =>
      sortDirectoryRepositories(
        directoryRepositories.filter((item) => item.is_active && item.work_directory === selectedWorkDirectory?.id)
      ),
    [directoryRepositories, selectedWorkDirectory?.id]
  );
  const selectedDirectoryMounts = useMemo(
    () => workerMounts.filter((mount) => mount.is_active && mount.work_directory === selectedWorkDirectory?.id),
    [selectedWorkDirectory?.id, workerMounts]
  );
  const selectedWorkerMounts = useMemo(
    () => workerMounts.filter((mount) => mount.is_active && mount.worker_card === selectedWorker?.id),
    [selectedWorker?.id, workerMounts]
  );

  const title =
    activeView === "workers"
      ? t("project_settings.agents.workers_page_title")
      : t("project_settings.agents.work_directories_page_title");
  const subtitle =
    activeView === "workers"
      ? t("project_settings.agents.workers_page_description")
      : t("project_settings.agents.work_directories_page_description");

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

  const handleCreateWorkerCard = async (formData: FormData) => {
    await submit("create-worker", async () => {
      const worker = await agentPlatformService.createWorkerCard(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        worker_endpoint: valueOf(formData, "worker_endpoint"),
        capabilities: csvOf(formData, "capabilities"),
      });
      setSelectedWorkerId(worker.id);
    });
  };

  const handleUpdateWorkerCard = async (formData: FormData) => {
    if (!selectedWorker) return;
    await submit("update-worker", async () => {
      await agentPlatformService.updateWorkerCard(workspaceSlug, selectedWorker.id, {
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        worker_endpoint: valueOf(formData, "worker_endpoint"),
        capabilities: csvOf(formData, "capabilities"),
        is_active: formData.get("is_active") === "on",
      });
    });
  };

  const handleCreateWorkDirectory = async (formData: FormData) => {
    await submit("create-work-directory", async () => {
      const directory = await agentPlatformService.createWorkDirectory(workspaceSlug, {
        key: valueOf(formData, "key"),
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        root_path: valueOf(formData, "root_path"),
        default_worker_card: optionalValueOf(formData, "default_worker_card"),
        worktree_strategy: valueOf(formData, "worktree_strategy") || "per_task",
        prd_path: valueOf(formData, "prd_path") || "prd.md",
        status_path: valueOf(formData, "status_path") || "status.md",
        progress_path: valueOf(formData, "progress_path") || "progress.md",
        is_active: true,
      });
      setSelectedWorkDirectoryId(directory.id);
    });
  };

  const handleUpdateWorkDirectory = async (formData: FormData) => {
    if (!selectedWorkDirectory) return;
    await submit("update-work-directory", async () => {
      await agentPlatformService.updateWorkDirectory(workspaceSlug, selectedWorkDirectory.id, {
        name: valueOf(formData, "name"),
        description: valueOf(formData, "description"),
        root_path: valueOf(formData, "root_path"),
        default_worker_card: optionalValueOf(formData, "default_worker_card"),
        worktree_strategy: valueOf(formData, "worktree_strategy") || "per_task",
        prd_path: valueOf(formData, "prd_path") || "prd.md",
        status_path: valueOf(formData, "status_path") || "status.md",
        progress_path: valueOf(formData, "progress_path") || "progress.md",
        is_active: formData.get("is_active") === "on",
      });
    });
  };

  const handleCreateRepository = async (formData: FormData) => {
    await submit("create-repository", async () => {
      await agentPlatformService.createRepository(workspaceSlug, {
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
        is_active: true,
      });
    });
  };

  const handleAttachRepository = async (formData: FormData) => {
    await submit("attach-repository", async () => {
      await agentPlatformService.createWorkDirectoryRepository(workspaceSlug, {
        work_directory: valueOf(formData, "work_directory"),
        repository: valueOf(formData, "repository"),
        relative_path: valueOf(formData, "relative_path") || ".",
        default_branch: valueOf(formData, "default_branch"),
        worktree_strategy: valueOf(formData, "worktree_strategy"),
        sort_order: Number(valueOf(formData, "sort_order") || 0),
        is_required: formData.get("is_required") === "on",
        is_active: true,
      });
    });
  };

  const handleCreateWorkerMount = async (formData: FormData) => {
    await submit("create-mount", async () => {
      await agentPlatformService.createWorkerMount(workspaceSlug, {
        work_directory: valueOf(formData, "work_directory"),
        worker_card: valueOf(formData, "worker_card"),
        local_path: valueOf(formData, "local_path"),
        is_default: formData.get("is_default") === "on",
        is_active: true,
      });
    });
  };

  return (
    <>
      <AppHeader
        header={
          <div className="flex items-center justify-between gap-3 px-5 py-3">
            <div className="flex min-w-0 items-center gap-2">
              {activeView === "workers" ? (
                <HardDrive className="size-4 shrink-0 text-secondary" />
              ) : (
                <FolderGit2 className="size-4 shrink-0 text-secondary" />
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
              <SegmentButton active={activeView === "workers"} onClick={() => setActiveView("workers")}>
                <HardDrive className="size-3.5" />
                {t("project_settings.agents.worker_cards")}
              </SegmentButton>
              <SegmentButton
                active={activeView === "work-directories"}
                onClick={() => setActiveView("work-directories")}
              >
                <FolderGit2 className="size-3.5" />
                {t("project_settings.agents.work_directories")}
              </SegmentButton>
            </div>
            <div className="flex flex-wrap gap-2 text-body-sm-regular text-secondary">
              <Metric label={t("project_settings.agents.worker_cards")} value={activeWorkers.length} />
              <Metric label={t("project_settings.agents.work_directories")} value={activeWorkDirectories.length} />
              <Metric label={t("project_settings.agents.repositories")} value={activeRepositories.length} />
              <Metric label={t("project_settings.agents.mounts")} value={workerMounts.length} />
            </div>
          </div>

          {isLoading ? (
            <EmptyState message={t("common.loading")} />
          ) : activeView === "workers" ? (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.35fr)]">
              <section className="min-w-0">
                <SectionHeader
                  icon={<Plus className="size-4" />}
                  title={t("project_settings.agents.create_worker")}
                  description={t("project_settings.agents.create_worker_description")}
                />
                <Form onSubmit={handleCreateWorkerCard}>
                  <Field name="key" label={t("project_settings.agents.key")} placeholder="mac-studio" />
                  <Field name="name" label={t("common.name")} placeholder="Mac Studio Worker" />
                  <Field
                    name="worker_endpoint"
                    label={t("project_settings.agents.worker_endpoint")}
                    placeholder="http://80.251.222.30:3112/workers/mac-studio"
                  />
                  <Field
                    name="capabilities"
                    label={t("project_settings.agents.capabilities")}
                    placeholder="codex, docker, git, macos"
                  />
                  <TextArea name="description" label={t("common.description")} rows={3} />
                  <SubmitButton
                    disabled={saving === "create-worker"}
                    icon={<Plus className="size-3.5" />}
                    label={t("project_settings.agents.create_worker")}
                  />
                </Form>
              </section>

              <section className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <SelectableList
                  empty={t("project_settings.agents.no_workers")}
                  icon={<HardDrive className="size-4" />}
                  items={activeWorkers.map((worker) => ({
                    id: worker.id,
                    title: worker.name,
                    description: worker.description || worker.worker_endpoint,
                    meta: `${worker.key} · ${worker.capabilities?.join(", ") || "-"}`,
                    active: worker.id === selectedWorker?.id,
                    status: worker.is_active
                      ? t("project_settings.agents.active")
                      : t("project_settings.agents.inactive"),
                  }))}
                  onSelect={setSelectedWorkerId}
                  title={t("project_settings.agents.worker_cards")}
                />

                <div className="min-w-0">
                  <SectionHeader
                    icon={<Pencil className="size-4" />}
                    title={selectedWorker?.name ?? t("project_settings.agents.worker_detail")}
                    description={t("project_settings.agents.worker_detail_description")}
                  />
                  {selectedWorker ? (
                    <div className="grid gap-4">
                      <Form key={selectedWorker.id} onSubmit={handleUpdateWorkerCard}>
                        <Field name="name" label={t("common.name")} defaultValue={selectedWorker.name} />
                        <Field
                          name="worker_endpoint"
                          label={t("project_settings.agents.worker_endpoint")}
                          defaultValue={selectedWorker.worker_endpoint}
                        />
                        <Field
                          name="capabilities"
                          label={t("project_settings.agents.capabilities")}
                          defaultValue={selectedWorker.capabilities?.join(", ")}
                        />
                        <TextArea
                          name="description"
                          label={t("common.description")}
                          rows={3}
                          defaultValue={selectedWorker.description}
                        />
                        <Checkbox
                          name="is_active"
                          label={t("project_settings.agents.active")}
                          defaultChecked={selectedWorker.is_active}
                        />
                        <SubmitButton
                          disabled={saving === "update-worker"}
                          icon={<Pencil className="size-3.5" />}
                          label={t("project_settings.agents.update_worker")}
                        />
                      </Form>
                      <ReadOnlyCards
                        empty={t("project_settings.agents.no_mounts")}
                        icon={<FolderGit2 className="size-4" />}
                        items={selectedWorkerMounts.map((mount) => ({
                          id: mount.id,
                          title: mount.work_directory_key || mount.work_directory,
                          meta: mount.is_default
                            ? t("project_settings.agents.default_mount")
                            : t("project_settings.agents.mount"),
                          description: mount.local_path,
                        }))}
                        title={t("project_settings.agents.worker_mounts")}
                      />
                    </div>
                  ) : (
                    <EmptyState message={t("project_settings.agents.no_workers")} />
                  )}
                </div>
              </section>
            </div>
          ) : (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.35fr)]">
              <section className="grid min-w-0 gap-5">
                <div>
                  <SectionHeader
                    icon={<Plus className="size-4" />}
                    title={t("project_settings.agents.create_work_directory")}
                    description={t("project_settings.agents.create_work_directory_description")}
                  />
                  <Form onSubmit={handleCreateWorkDirectory}>
                    <Field name="key" label={t("project_settings.agents.key")} placeholder="agent-control-plane" />
                    <Field name="name" label={t("common.name")} placeholder="Agent Control Plane" />
                    <Field
                      name="root_path"
                      label={t("project_settings.agents.root_path")}
                      placeholder="/Users/a/agent-worker-workspaces/agent-control-plane"
                    />
                    <EntitySelect
                      label={t("project_settings.agents.default_worker")}
                      name="default_worker_card"
                      optional
                      values={activeWorkers.map((worker) => ({ id: worker.id, name: worker.name }))}
                    />
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field name="worktree_strategy" label="Worktree strategy" defaultValue="per_task" />
                      <Field name="prd_path" label="prd.md" defaultValue="prd.md" />
                      <Field name="status_path" label="status.md" defaultValue="status.md" />
                      <Field name="progress_path" label="progress.md" defaultValue="progress.md" />
                    </div>
                    <TextArea name="description" label={t("common.description")} rows={3} />
                    <SubmitButton
                      disabled={saving === "create-work-directory"}
                      icon={<Plus className="size-3.5" />}
                      label={t("project_settings.agents.create_work_directory")}
                    />
                  </Form>
                </div>

                <div>
                  <SectionHeader
                    icon={<GitBranch className="size-4" />}
                    title={t("project_settings.agents.create_repository")}
                    description={t("project_settings.agents.create_repository_description")}
                  />
                  <Form onSubmit={handleCreateRepository}>
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field name="key" label={t("project_settings.agents.key")} placeholder="plane" />
                      <Field name="provider" label="Provider" placeholder="github" defaultValue="github" />
                      <Field name="owner" label="Owner" placeholder="michaelx1993" />
                      <Field name="name" label={t("common.name")} placeholder="plane" />
                    </div>
                    <Field name="full_name" label="Full name" placeholder="michaelx1993/plane" />
                    <Field name="url" label="Clone URL" placeholder="git@github.com:michaelx1993/plane.git" required />
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field
                        name="default_branch"
                        label={t("project_settings.agents.default_branch")}
                        defaultValue="default"
                      />
                      <Field name="credential_key" label="Credential key" placeholder="github-token" />
                      <Field name="worktree_strategy" label="Worktree strategy" defaultValue="per_run" />
                      <Field
                        name="local_path"
                        label={t("project_settings.agents.local_path")}
                        placeholder="/Users/a/plane"
                      />
                    </div>
                    <Checkbox
                      name="is_required"
                      label={t("project_settings.agents.required_for_phase_1")}
                      defaultChecked
                    />
                    <SubmitButton
                      disabled={saving === "create-repository"}
                      icon={<Plus className="size-3.5" />}
                      label={t("project_settings.agents.create_repository")}
                    />
                  </Form>
                </div>
              </section>

              <section className="grid min-w-0 gap-5">
                <div className="grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                  <SelectableList
                    empty={t("project_settings.agents.no_work_directories")}
                    icon={<FolderGit2 className="size-4" />}
                    items={activeWorkDirectories.map((directory) => ({
                      id: directory.id,
                      title: directory.name,
                      description: directory.root_path || directory.description,
                      meta: `${directory.key} · ${directory.worktree_strategy} · ${directory.repository_count ?? 0} repo`,
                      active: directory.id === selectedWorkDirectory?.id,
                      status: directory.is_active
                        ? t("project_settings.agents.active")
                        : t("project_settings.agents.inactive"),
                    }))}
                    onSelect={setSelectedWorkDirectoryId}
                    title={t("project_settings.agents.work_directories")}
                  />

                  <div className="min-w-0">
                    <SectionHeader
                      icon={<Pencil className="size-4" />}
                      title={selectedWorkDirectory?.name ?? t("project_settings.agents.work_directory_detail")}
                      description={t("project_settings.agents.work_directory_detail_description")}
                    />
                    {selectedWorkDirectory ? (
                      <Form key={selectedWorkDirectory.id} onSubmit={handleUpdateWorkDirectory}>
                        <Field name="name" label={t("common.name")} defaultValue={selectedWorkDirectory.name} />
                        <Field
                          name="root_path"
                          label={t("project_settings.agents.root_path")}
                          defaultValue={selectedWorkDirectory.root_path}
                        />
                        <EntitySelect
                          defaultValue={selectedWorkDirectory.default_worker_card ?? ""}
                          label={t("project_settings.agents.default_worker")}
                          name="default_worker_card"
                          optional
                          values={activeWorkers.map((worker) => ({ id: worker.id, name: worker.name }))}
                        />
                        <div className="grid gap-3 md:grid-cols-2">
                          <Field
                            name="worktree_strategy"
                            label="Worktree strategy"
                            defaultValue={selectedWorkDirectory.worktree_strategy}
                          />
                          <Field name="prd_path" label="prd.md" defaultValue={selectedWorkDirectory.prd_path} />
                          <Field
                            name="status_path"
                            label="status.md"
                            defaultValue={selectedWorkDirectory.status_path}
                          />
                          <Field
                            name="progress_path"
                            label="progress.md"
                            defaultValue={selectedWorkDirectory.progress_path}
                          />
                        </div>
                        <TextArea
                          name="description"
                          label={t("common.description")}
                          rows={3}
                          defaultValue={selectedWorkDirectory.description}
                        />
                        <Checkbox
                          name="is_active"
                          label={t("project_settings.agents.active")}
                          defaultChecked={selectedWorkDirectory.is_active}
                        />
                        <SubmitButton
                          disabled={saving === "update-work-directory"}
                          icon={<Pencil className="size-3.5" />}
                          label={t("project_settings.agents.update_work_directory")}
                        />
                      </Form>
                    ) : (
                      <EmptyState message={t("project_settings.agents.no_work_directories")} />
                    )}
                  </div>
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                  <div>
                    <SectionHeader
                      icon={<Link2 className="size-4" />}
                      title={t("project_settings.agents.attach_repository")}
                      description={t("project_settings.agents.attach_repository_description")}
                    />
                    <Form onSubmit={handleAttachRepository}>
                      <EntitySelect
                        defaultValue={selectedWorkDirectory?.id}
                        label={t("project_settings.agents.work_directory")}
                        name="work_directory"
                        values={activeWorkDirectories.map((directory) => ({ id: directory.id, name: directory.name }))}
                      />
                      <EntitySelect
                        label={t("project_settings.agents.repository")}
                        name="repository"
                        values={activeRepositories.map((repository) => ({
                          id: repository.id,
                          name: repository.full_name || repository.name,
                        }))}
                      />
                      <div className="grid gap-3 md:grid-cols-2">
                        <Field
                          name="relative_path"
                          label={t("project_settings.agents.relative_path")}
                          defaultValue="."
                        />
                        <Field name="default_branch" label={t("project_settings.agents.default_branch")} />
                        <Field name="worktree_strategy" label="Worktree strategy" />
                        <Field name="sort_order" label={t("workspace_settings.settings.agents.order")} type="number" />
                      </div>
                      <Checkbox
                        name="is_required"
                        label={t("project_settings.agents.required_for_phase_1")}
                        defaultChecked
                      />
                      <SubmitButton
                        disabled={saving === "attach-repository"}
                        icon={<Link2 className="size-3.5" />}
                        label={t("project_settings.agents.attach_repository")}
                      />
                    </Form>
                  </div>

                  <div>
                    <SectionHeader
                      icon={<Server className="size-4" />}
                      title={t("project_settings.agents.create_mount")}
                      description={t("project_settings.agents.create_mount_description")}
                    />
                    <Form onSubmit={handleCreateWorkerMount}>
                      <EntitySelect
                        defaultValue={selectedWorkDirectory?.id}
                        label={t("project_settings.agents.work_directory")}
                        name="work_directory"
                        values={activeWorkDirectories.map((directory) => ({ id: directory.id, name: directory.name }))}
                      />
                      <EntitySelect
                        label={t("project_settings.agents.worker_cards")}
                        name="worker_card"
                        values={activeWorkers.map((worker) => ({ id: worker.id, name: worker.name }))}
                      />
                      <Field
                        name="local_path"
                        label={t("project_settings.agents.local_path")}
                        placeholder="/Users/a/agent-worker-workspaces/plane"
                      />
                      <Checkbox name="is_default" label={t("project_settings.agents.default_mount")} />
                      <SubmitButton
                        disabled={saving === "create-mount"}
                        icon={<Plus className="size-3.5" />}
                        label={t("project_settings.agents.create_mount")}
                      />
                    </Form>
                  </div>
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                  <ReadOnlyCards
                    empty={t("project_settings.agents.no_directory_repositories")}
                    icon={<GitBranch className="size-4" />}
                    items={selectedDirectoryRepositories.map((link) => ({
                      id: link.id,
                      title: link.repository_name || link.repository_key || link.repository,
                      meta: `${link.relative_path} · ${link.default_branch || "default"} · ${
                        link.worktree_strategy || "per_run"
                      }`,
                      description: link.repository_url,
                    }))}
                    title={t("project_settings.agents.directory_repositories")}
                  />
                  <ReadOnlyCards
                    empty={t("project_settings.agents.no_mounts")}
                    icon={<Server className="size-4" />}
                    items={selectedDirectoryMounts.map((mount) => ({
                      id: mount.id,
                      title: mount.worker_name || mount.worker_key || mount.worker_card,
                      meta: mount.is_default
                        ? t("project_settings.agents.default_mount")
                        : t("project_settings.agents.mount"),
                      description: mount.local_path,
                    }))}
                    title={t("project_settings.agents.worker_mounts")}
                  />
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
        required={props.required ?? (props.name === "key" || props.name === "name" || props.name === "local_path")}
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

function EntitySelect(props: {
  defaultValue?: string;
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
        defaultValue={props.defaultValue}
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

function SelectableList(props: {
  empty: string;
  icon: React.ReactNode;
  items: Array<{ active: boolean; description?: string; id: string; meta: string; status: string; title: string }>;
  onSelect: (id: string) => void;
  title: string;
}) {
  return (
    <div className="min-w-0">
      <SectionHeader icon={props.icon} title={props.title} />
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
                <span className="truncate text-body-sm-medium text-primary">{item.title}</span>
                <span className="text-caption-regular shrink-0 text-tertiary">{item.status}</span>
              </div>
              <div className="mt-1 truncate text-body-xs-regular text-secondary">{item.meta}</div>
              {item.description && (
                <p className="mt-1 line-clamp-2 text-body-xs-regular text-tertiary">{item.description}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ReadOnlyCards(props: {
  empty: string;
  icon: React.ReactNode;
  items: Array<{ description?: string; id: string; meta: string; title: string }>;
  title: string;
}) {
  return (
    <section className="min-w-0">
      <SectionHeader icon={props.icon} title={props.title} />
      {props.items.length === 0 ? (
        <EmptyState message={props.empty} />
      ) : (
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
      )}
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

function sortDirectoryRepositories(items: AgentWorkDirectoryRepository[]): AgentWorkDirectoryRepository[] {
  const sorted = Array.from(items);
  sorted.sort(
    (a, b) => a.sort_order - b.sort_order || (a.repository_name ?? "").localeCompare(b.repository_name ?? "")
  );
  return sorted;
}
