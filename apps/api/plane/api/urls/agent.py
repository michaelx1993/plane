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
    AgentProjectWorkspaceDetailAPIEndpoint,
    AgentProjectWorkspaceListCreateAPIEndpoint,
    AgentRepositoryDetailAPIEndpoint,
    AgentRepositoryListCreateAPIEndpoint,
    AgentRoleDetailAPIEndpoint,
    AgentRoleListCreateAPIEndpoint,
    AgentUserAgentDetailAPIEndpoint,
    AgentUserAgentListCreateAPIEndpoint,
    AgentWorkerCardDetailAPIEndpoint,
    AgentWorkerCardListCreateAPIEndpoint,
)

urlpatterns = [
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
