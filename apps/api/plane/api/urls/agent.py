# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path

from plane.api.views import (
    AgentConfigOutboxAPIEndpoint,
    AgentPromptBindingDetailAPIEndpoint,
    AgentPromptBindingListCreateAPIEndpoint,
    AgentPromptDetailAPIEndpoint,
    AgentPromptListCreateAPIEndpoint,
    AgentPromptVersionDetailAPIEndpoint,
    AgentPromptVersionListCreateAPIEndpoint,
    AgentProjectDefaultDetailAPIEndpoint,
    AgentProjectDefaultListCreateAPIEndpoint,
    AgentProjectWorkspaceDetailAPIEndpoint,
    AgentProjectWorkspaceListCreateAPIEndpoint,
    AgentRepositoryDetailAPIEndpoint,
    AgentRepositoryListCreateAPIEndpoint,
    AgentRoleDetailAPIEndpoint,
    AgentRoleListCreateAPIEndpoint,
    AgentRunIntentAPIEndpoint,
    AgentTaskContextDocumentDetailAPIEndpoint,
    AgentTaskContextDocumentListCreateAPIEndpoint,
    AgentTaskContextDocumentVersionListAPIEndpoint,
    AgentTaskContextSnapshotAPIEndpoint,
    AgentTaskProgressEntryListCreateAPIEndpoint,
    AgentTaskWorkflowActionAPIEndpoint,
    AgentTaskWorkflowInstanceDetailAPIEndpoint,
    AgentTaskWorkflowInstanceListCreateAPIEndpoint,
    AgentTaskWorkflowNodeDetailAPIEndpoint,
    AgentTaskWorkflowNodeListAPIEndpoint,
    AgentTaskWorkflowTransitionListAPIEndpoint,
    AgentTaskWorkDirectoryOverrideDetailAPIEndpoint,
    AgentTaskWorkDirectoryOverrideListCreateAPIEndpoint,
    AgentUserAgentDetailAPIEndpoint,
    AgentUserAgentListCreateAPIEndpoint,
    AgentUserSecretKeyDetailAPIEndpoint,
    AgentUserSecretKeyListCreateAPIEndpoint,
    AgentWorkDirectoryDetailAPIEndpoint,
    AgentWorkDirectoryListCreateAPIEndpoint,
    AgentWorkDirectoryRepositoryDetailAPIEndpoint,
    AgentWorkDirectoryRepositoryListCreateAPIEndpoint,
    AgentWorkerCardDetailAPIEndpoint,
    AgentWorkerCardListCreateAPIEndpoint,
    AgentWorkerMountDetailAPIEndpoint,
    AgentWorkerMountListCreateAPIEndpoint,
    AgentWorkDirectoryResolutionAPIEndpoint,
)

urlpatterns = [
    path(
        "workspaces/<str:slug>/agent-runs/",
        AgentRunIntentAPIEndpoint.as_view(http_method_names=["post"]),
        name="agent-run-intent",
    ),
    path(
        "workspaces/<str:slug>/agent-config-outbox/",
        AgentConfigOutboxAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-config-outbox",
    ),
    path(
        "workspaces/<str:slug>/agent-agents/",
        AgentUserAgentListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-user-agent",
    ),
    path(
        "workspaces/<str:slug>/agent-agents/<uuid:pk>/",
        AgentUserAgentDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-user-agent",
    ),
    path(
        "workspaces/<str:slug>/agent-prompts/",
        AgentPromptListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-prompt",
    ),
    path(
        "workspaces/<str:slug>/agent-prompts/<uuid:pk>/",
        AgentPromptDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-prompt",
    ),
    path(
        "workspaces/<str:slug>/agent-prompt-versions/",
        AgentPromptVersionListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-prompt-version",
    ),
    path(
        "workspaces/<str:slug>/agent-prompt-versions/<uuid:pk>/",
        AgentPromptVersionDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-prompt-version",
    ),
    path(
        "workspaces/<str:slug>/agent-roles/",
        AgentRoleListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-role",
    ),
    path(
        "workspaces/<str:slug>/agent-roles/<uuid:pk>/",
        AgentRoleDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-role",
    ),
    path(
        "workspaces/<str:slug>/agent-prompt-bindings/",
        AgentPromptBindingListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-prompt-binding",
    ),
    path(
        "workspaces/<str:slug>/agent-prompt-bindings/<uuid:pk>/",
        AgentPromptBindingDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-prompt-binding",
    ),
    path(
        "workspaces/<str:slug>/agent-worker-cards/",
        AgentWorkerCardListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-worker-card",
    ),
    path(
        "workspaces/<str:slug>/agent-worker-cards/<uuid:pk>/",
        AgentWorkerCardDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-worker-card",
    ),
    path(
        "workspaces/<str:slug>/agent-work-directories/",
        AgentWorkDirectoryListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-work-directory",
    ),
    path(
        "workspaces/<str:slug>/agent-work-directories/<uuid:pk>/",
        AgentWorkDirectoryDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-work-directory",
    ),
    path(
        "workspaces/<str:slug>/agent-work-directory-repositories/",
        AgentWorkDirectoryRepositoryListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-work-directory-repository",
    ),
    path(
        "workspaces/<str:slug>/agent-work-directory-repositories/<uuid:pk>/",
        AgentWorkDirectoryRepositoryDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-work-directory-repository",
    ),
    path(
        "workspaces/<str:slug>/agent-worker-mounts/",
        AgentWorkerMountListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-worker-mount",
    ),
    path(
        "workspaces/<str:slug>/agent-worker-mounts/<uuid:pk>/",
        AgentWorkerMountDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-worker-mount",
    ),
    path(
        "workspaces/<str:slug>/agent-project-defaults/",
        AgentProjectDefaultListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-project-default",
    ),
    path(
        "workspaces/<str:slug>/agent-project-defaults/<uuid:pk>/",
        AgentProjectDefaultDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-project-default",
    ),
    path(
        "workspaces/<str:slug>/agent-task-work-directory-overrides/",
        AgentTaskWorkDirectoryOverrideListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-task-work-directory-override",
    ),
    path(
        "workspaces/<str:slug>/agent-task-work-directory-overrides/<uuid:pk>/",
        AgentTaskWorkDirectoryOverrideDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-task-work-directory-override",
    ),
    path(
        "workspaces/<str:slug>/agent-task-context-documents/",
        AgentTaskContextDocumentListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-task-context-document",
    ),
    path(
        "workspaces/<str:slug>/agent-task-context-documents/<uuid:pk>/",
        AgentTaskContextDocumentDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-task-context-document",
    ),
    path(
        "workspaces/<str:slug>/agent-task-context-document-versions/",
        AgentTaskContextDocumentVersionListAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-task-context-document-version",
    ),
    path(
        "workspaces/<str:slug>/agent-task-progress-entries/",
        AgentTaskProgressEntryListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-task-progress-entry",
    ),
    path(
        "workspaces/<str:slug>/agent-task-context-snapshot/",
        AgentTaskContextSnapshotAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-task-context-snapshot",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-instances/",
        AgentTaskWorkflowInstanceListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-task-workflow-instance",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-instances/<uuid:pk>/",
        AgentTaskWorkflowInstanceDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-task-workflow-instance",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-nodes/",
        AgentTaskWorkflowNodeListAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-task-workflow-node",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-nodes/<uuid:pk>/",
        AgentTaskWorkflowNodeDetailAPIEndpoint.as_view(http_method_names=["get", "patch"]),
        name="agent-task-workflow-node",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-transitions/",
        AgentTaskWorkflowTransitionListAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-task-workflow-transition",
    ),
    path(
        "workspaces/<str:slug>/agent-task-workflow-actions/",
        AgentTaskWorkflowActionAPIEndpoint.as_view(http_method_names=["post"]),
        name="agent-task-workflow-action",
    ),
    path(
        "workspaces/<str:slug>/agent-work-directory-resolution/",
        AgentWorkDirectoryResolutionAPIEndpoint.as_view(http_method_names=["get"]),
        name="agent-work-directory-resolution",
    ),
    path(
        "workspaces/<str:slug>/agent-user-secret-keys/",
        AgentUserSecretKeyListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-user-secret-key",
    ),
    path(
        "workspaces/<str:slug>/agent-user-secret-keys/<uuid:pk>/",
        AgentUserSecretKeyDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-user-secret-key",
    ),
    path(
        "workspaces/<str:slug>/agent-project-workspaces/",
        AgentProjectWorkspaceListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-project-workspace",
    ),
    path(
        "workspaces/<str:slug>/agent-project-workspaces/<uuid:pk>/",
        AgentProjectWorkspaceDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-project-workspace",
    ),
    path(
        "workspaces/<str:slug>/agent-repositories/",
        AgentRepositoryListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="agent-repository",
    ),
    path(
        "workspaces/<str:slug>/agent-repositories/<uuid:pk>/",
        AgentRepositoryDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="agent-repository",
    ),
]
