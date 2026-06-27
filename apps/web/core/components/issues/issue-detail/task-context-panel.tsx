/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useMemo, useState } from "react";
import { FileText, MessageSquareText, Pencil, Plus, RefreshCw, Save } from "lucide-react";
import useSWR from "swr";
// plane imports
import { useTranslation } from "@plane/i18n";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// components
import { MarkdownRenderer } from "@/components/ui/markdown-to-component";
// services
import {
  AgentPlatformService,
  type AgentTaskContextDocument,
  type AgentTaskContextDocumentType,
  type AgentTaskContextSnapshot,
  type AgentTaskProgressEntry,
  type AgentTaskWorkflowInstance,
} from "@/services/agent-platform.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled: boolean;
};

const agentPlatformService = new AgentPlatformService();

export function TaskContextPanel(props: Props) {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const { t } = useTranslation();
  const [isMounted, setIsMounted] = useState(false);
  const [progressDraft, setProgressDraft] = useState("");
  const [isAppendingProgress, setIsAppendingProgress] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const snapshotKey = isMounted ? `TASK_CONTEXT_SNAPSHOT_${workspaceSlug}_${projectId}_${issueId}` : null;
  const workflowKey = isMounted ? `TASK_CONTEXT_WORKFLOW_${workspaceSlug}_${issueId}` : null;
  const {
    data: snapshot,
    error: snapshotError,
    isLoading: isSnapshotLoading,
    mutate: mutateSnapshot,
  } = useSWR<AgentTaskContextSnapshot | null>(snapshotKey, () =>
    agentPlatformService.getTaskContextSnapshot(workspaceSlug, projectId, issueId)
  );
  const { data: workflows, isLoading: isWorkflowLoading } = useSWR<AgentTaskWorkflowInstance[]>(workflowKey, () =>
    agentPlatformService.listTaskWorkflowInstances(workspaceSlug, issueId)
  );

  const activeWorkflow = useMemo(
    () => workflows?.find((workflow) => workflow.status === "active") ?? workflows?.[0],
    [workflows]
  );
  const activeNode = useMemo(
    () =>
      activeWorkflow?.nodes.find((node) => node.id === activeWorkflow.active_node) ??
      activeWorkflow?.nodes.find((node) => node.status === "active") ??
      null,
    [activeWorkflow]
  );
  const canEditPrd = !disabled && (!activeNode || activeNode.key === "intake");
  const isLoading = isSnapshotLoading || isWorkflowLoading;

  const appendProgress = async () => {
    const body = progressDraft.trim();
    if (!body || disabled || isAppendingProgress) return;

    setIsAppendingProgress(true);
    try {
      await agentPlatformService.createTaskProgressEntry(workspaceSlug, {
        issue: issueId,
        entry_type: "progress",
        source: "human",
        body,
        summary: firstLine(body),
        node_key: activeNode?.key ?? "",
      });
      setProgressDraft("");
      await mutateSnapshot();
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: t("common.success"),
        message: t("issue.task_context.progress_appended"),
      });
    } catch {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: t("common.error"),
        message: t("issue.task_context.progress_append_failed"),
      });
    } finally {
      setIsAppendingProgress(false);
    }
  };

  if (!isMounted) return null;

  return (
    <section className="rounded-lg border border-subtle bg-surface-1" data-testid="task-context-panel">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-subtle px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-body-sm-medium text-primary">
            <FileText className="h-4 w-4 flex-shrink-0" strokeWidth={2} />
            {t("issue.task_context.title")}
          </div>
          <p className="mt-1 text-body-xs-regular text-secondary">{t("issue.task_context.description")}</p>
        </div>
        <button
          className="inline-flex min-h-8 items-center gap-1 rounded border border-subtle px-2 text-body-xs-medium text-secondary hover:bg-surface-2"
          disabled={isLoading}
          onClick={() => mutateSnapshot()}
          type="button"
        >
          <RefreshCw className="h-3.5 w-3.5" strokeWidth={2} />
          {t("common.refresh")}
        </button>
      </div>

      {snapshotError ? (
        <div className="px-4 py-3 text-body-sm-regular text-tertiary">{t("issue.task_context.unavailable")}</div>
      ) : isLoading ? (
        <div className="px-4 py-3 text-body-sm-regular text-tertiary">{t("common.loading")}</div>
      ) : snapshot ? (
        <div className="grid gap-4 p-4">
          <TaskContextHeader snapshot={snapshot} workflow={activeWorkflow} activeNode={activeNode} />

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <DocumentCard
              document={snapshot.documents.status}
              documentType="status"
              disabled={disabled}
              emptyBody={t("issue.task_context.empty_status")}
              onSaved={mutateSnapshot}
              title={t("issue.task_context.status_title")}
              workspaceSlug={workspaceSlug}
              issueId={issueId}
            />
            <DocumentCard
              document={snapshot.documents.prd}
              documentType="prd"
              disabled={!canEditPrd}
              disabledReason={activeNode && activeNode.key !== "intake" ? t("issue.task_context.prd_locked") : ""}
              emptyBody={t("issue.task_context.empty_prd")}
              onSaved={mutateSnapshot}
              title={t("issue.task_context.prd_title")}
              workspaceSlug={workspaceSlug}
              issueId={issueId}
            />
          </div>

          <ProgressSection
            disabled={disabled || isAppendingProgress}
            draft={progressDraft}
            entries={snapshot.progressEntries}
            onAppend={appendProgress}
            onDraftChange={setProgressDraft}
          />

          <HumanContextSection comments={snapshot.humanComments} />
        </div>
      ) : (
        <div className="px-4 py-3 text-body-sm-regular text-tertiary">{t("issue.task_context.unavailable")}</div>
      )}
    </section>
  );
}

function TaskContextHeader(props: {
  snapshot: AgentTaskContextSnapshot;
  workflow?: AgentTaskWorkflowInstance;
  activeNode: AgentTaskWorkflowInstance["nodes"][number] | null;
}) {
  const { snapshot, workflow, activeNode } = props;
  const { t } = useTranslation();
  const workDirectory = snapshot.workDirectory.workDirectory;
  const worker = snapshot.workDirectory.worker;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
      <SummaryCell
        label={t("issue.task_context.active_node")}
        value={activeNode?.name || workflow?.active_node_name || "-"}
      />
      <SummaryCell
        label={t("issue.task_context.owner")}
        value={activeNode?.assigned_agent_name || activeNode?.owner_type || "-"}
      />
      <SummaryCell label={t("issue.task_context.work_directory")} value={workDirectory?.name || "-"} />
      <SummaryCell label={t("issue.task_context.worker")} value={worker?.name || "-"} />
    </div>
  );
}

function DocumentCard(props: {
  workspaceSlug: string;
  issueId: string;
  documentType: AgentTaskContextDocumentType;
  document: AgentTaskContextDocument | null;
  title: string;
  emptyBody: string;
  disabled: boolean;
  disabledReason?: string;
  onSaved: () => Promise<AgentTaskContextSnapshot | null | undefined>;
}) {
  const { workspaceSlug, issueId, documentType, document, title, emptyBody, disabled, disabledReason, onSaved } = props;
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(document?.body ?? "");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setDraft(document?.body ?? "");
  }, [document?.body]);

  const saveDocument = async () => {
    if (disabled || isSaving) return;
    setIsSaving(true);
    try {
      if (document) {
        await agentPlatformService.updateTaskContextDocument(workspaceSlug, document.id, {
          body: draft,
          body_format: "markdown",
          title: `${documentType}.md`,
        });
      } else {
        await agentPlatformService.createTaskContextDocument(workspaceSlug, {
          issue: issueId,
          document_type: documentType,
          title: `${documentType}.md`,
          body: draft,
          body_format: "markdown",
          is_active: true,
        });
      }
      setIsEditing(false);
      await onSaved();
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: t("common.success"),
        message: t("issue.task_context.document_saved"),
      });
    } catch {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: t("common.error"),
        message: t("issue.task_context.document_save_failed"),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const cancelEditing = () => {
    setDraft(document?.body ?? "");
    setIsEditing(false);
  };

  return (
    <article className="min-w-0 rounded border border-subtle bg-surface-2">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-subtle px-3 py-2">
        <div className="min-w-0">
          <h3 className="truncate text-body-sm-medium text-primary">{title}</h3>
          <div className="text-caption-regular mt-0.5 text-tertiary">
            {document ? `v${document.version} · ${document.path}` : `${documentType}.md`}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {disabledReason && <span className="text-caption-regular text-tertiary">{disabledReason}</span>}
          {isEditing ? (
            <>
              <button
                className="text-body-xs-medium text-secondary hover:text-primary"
                onClick={cancelEditing}
                type="button"
              >
                {t("common.cancel")}
              </button>
              <button
                className="bg-custom-primary-100 inline-flex min-h-8 items-center gap-1 rounded px-2 text-body-xs-medium text-white disabled:opacity-60"
                disabled={isSaving}
                onClick={saveDocument}
                type="button"
              >
                <Save className="h-3.5 w-3.5" strokeWidth={2} />
                {isSaving ? t("common.loading") : t("common.save")}
              </button>
            </>
          ) : (
            <button
              className="inline-flex min-h-8 items-center gap-1 rounded border border-subtle px-2 text-body-xs-medium text-secondary hover:bg-surface-1 disabled:opacity-60"
              disabled={disabled}
              onClick={() => setIsEditing(true)}
              type="button"
            >
              {document ? (
                <Pencil className="h-3.5 w-3.5" strokeWidth={2} />
              ) : (
                <Plus className="h-3.5 w-3.5" strokeWidth={2} />
              )}
              {document ? t("common.edit") : t("common.add")}
            </button>
          )}
        </div>
      </div>

      <div className="min-h-40 p-3">
        {isEditing ? (
          <textarea
            className="font-mono focus:border-custom-primary-100 min-h-56 w-full resize-y rounded border border-subtle bg-surface-1 p-3 text-body-sm-regular text-primary outline-none"
            onChange={(event) => setDraft(event.currentTarget.value)}
            placeholder={emptyBody}
            value={draft}
          />
        ) : document?.body ? (
          <div className="grid gap-2">
            <MarkdownRenderer markdown={document.body} />
          </div>
        ) : (
          <p className="text-body-sm-regular text-tertiary">{emptyBody}</p>
        )}
      </div>
    </article>
  );
}

function ProgressSection(props: {
  entries: AgentTaskProgressEntry[];
  draft: string;
  disabled: boolean;
  onDraftChange: (value: string) => void;
  onAppend: () => void;
}) {
  const { entries, draft, disabled, onDraftChange, onAppend } = props;
  const { t } = useTranslation();
  const recentEntries = takeLatestFirst(entries, 6);

  return (
    <section className="rounded border border-subtle bg-surface-2">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-subtle px-3 py-2">
        <div>
          <h3 className="text-body-sm-medium text-primary">{t("issue.task_context.progress_title")}</h3>
          <p className="text-caption-regular mt-0.5 text-tertiary">{t("issue.task_context.progress_append_only")}</p>
        </div>
        <span className="text-caption-regular text-tertiary">{entries.length}</span>
      </div>
      <div className="grid gap-3 p-3">
        <div className="grid gap-2">
          <textarea
            className="focus:border-custom-primary-100 min-h-24 w-full resize-y rounded border border-subtle bg-surface-1 p-3 text-body-sm-regular text-primary outline-none"
            disabled={disabled}
            onChange={(event) => onDraftChange(event.currentTarget.value)}
            placeholder={t("issue.task_context.progress_placeholder")}
            value={draft}
          />
          <div className="flex justify-end">
            <button
              className="bg-custom-primary-100 inline-flex min-h-8 items-center gap-1 rounded px-3 text-body-xs-medium text-white disabled:opacity-60"
              disabled={disabled || !draft.trim()}
              onClick={onAppend}
              type="button"
            >
              <Plus className="h-3.5 w-3.5" strokeWidth={2} />
              {t("issue.task_context.append_progress")}
            </button>
          </div>
        </div>

        {recentEntries.length > 0 ? (
          <div className="grid gap-2">
            {recentEntries.map((entry) => (
              <div key={entry.id} className="rounded border border-subtle bg-surface-1 p-3">
                <div className="text-caption-regular mb-1 flex flex-wrap items-center gap-2 text-tertiary">
                  <span>{entry.source}</span>
                  <span>{entry.entry_type}</span>
                  <span>{formatDateTime(entry.occurred_at || entry.created_at)}</span>
                  {entry.node_key && <span>{entry.node_key}</span>}
                </div>
                <div className="text-body-sm-regular whitespace-pre-wrap text-primary">{entry.body}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-body-sm-regular text-tertiary">{t("issue.task_context.empty_progress")}</p>
        )}
      </div>
    </section>
  );
}

function HumanContextSection(props: { comments: AgentTaskContextSnapshot["humanComments"] }) {
  const { comments } = props;
  const { t } = useTranslation();
  const recentComments = takeLatestFirst(comments, 4);

  return (
    <section className="rounded border border-subtle bg-surface-2 p-3">
      <div className="mb-2 flex items-center gap-2 text-body-sm-medium text-primary">
        <MessageSquareText className="h-4 w-4" strokeWidth={2} />
        {t("issue.task_context.human_context")}
      </div>
      {recentComments.length > 0 ? (
        <div className="grid gap-2">
          {recentComments.map((comment) => (
            <div key={comment.id} className="rounded border border-subtle bg-surface-1 p-3">
              <div className="text-caption-regular mb-1 text-tertiary">{formatDateTime(comment.createdAt)}</div>
              <div className="text-body-sm-regular text-primary">{comment.body}</div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-body-sm-regular text-tertiary">{t("issue.task_context.empty_human_context")}</p>
      )}
    </section>
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

function firstLine(value: string): string {
  return (
    value
      .split(/\r?\n/)
      .find((line) => line.trim())
      ?.trim() ?? value.trim()
  );
}

function takeLatestFirst<T>(items: T[], limit: number): T[] {
  const selected: T[] = [];
  const start = Math.max(items.length - limit, 0);
  for (let index = items.length - 1; index >= start; index -= 1) {
    selected.push(items[index]);
  }
  return selected;
}

function formatDateTime(value: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}
