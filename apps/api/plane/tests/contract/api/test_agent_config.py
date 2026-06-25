# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from rest_framework import status

from plane.api.views.agent import _agent_run_workflow_state
from plane.db.models import AgentConfigOutbox, AgentPrompt, AgentPromptBinding


@pytest.mark.contract
class TestAgentConfigAPI:
    def test_agent_run_workflow_state_maps_plane_state_groups(self):
        state = type("StateStub", (), {"name": "In Progress", "group": "started"})()
        assert _agent_run_workflow_state(state) == "Development"

        state = type("StateStub", (), {"name": "Cancelled", "group": "cancelled"})()
        assert _agent_run_workflow_state(state) == "Canceled"

    @pytest.mark.django_db
    def test_session_user_can_list_agent_config(self, session_client, workspace, create_user):
        session_client.force_authenticate(user=create_user)
        AgentPrompt.objects.create(
            workspace=workspace,
            key="rd-agent-base",
            name="RD Agent Base",
            scope="agent",
            kind="instruction",
        )

        response = session_client.get(f"/api/v1/workspaces/{workspace.slug}/agent-prompts/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["key"] == "rd-agent-base"

    @pytest.mark.django_db
    def test_create_agent_writes_config_outbox(self, api_key_client, workspace, create_user):
        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-agents/",
            {
                "key": "codex-default",
                "name": "Codex Default",
                "description": "Default development agent",
                "runtime": "codex",
                "owner": str(create_user.id),
                "tools": ["github", "shell"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Got {response.status_code}: {response.data!r}"

        outbox = AgentConfigOutbox.objects.get()
        assert outbox.workspace == workspace
        assert outbox.entity_type == "agent_user_agent"
        assert outbox.operation == "create"
        assert outbox.payload["key"] == "codex-default"

        outbox_response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-config-outbox/?after_id=0&limit=10"
        )

        assert outbox_response.status_code == status.HTTP_200_OK
        assert outbox_response.data[0]["id"] == outbox.id
        assert outbox_response.data[0]["payload"]["key"] == "codex-default"

    @pytest.mark.django_db
    def test_create_prompt_version_updates_latest_version_and_outbox(self, api_key_client, workspace):
        prompt_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompts/",
            {
                "key": "rd-agent-base",
                "name": "RD Agent Base",
                "scope": "agent",
                "kind": "instruction",
                "description": "Base development behavior",
            },
            format="json",
        )
        assert prompt_response.status_code == status.HTTP_201_CREATED

        version_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-versions/",
            {
                "prompt": prompt_response.data["id"],
                "version": 1,
                "body": "You are the development agent.",
                "variables": ["repo", "task"],
            },
            format="json",
        )

        assert version_response.status_code == status.HTTP_201_CREATED, (
            f"Got {version_response.status_code}: {version_response.data!r}"
        )

        prompt = AgentPrompt.objects.get(id=prompt_response.data["id"])
        assert prompt.latest_version == 1
        assert prompt.scope == "agent"
        assert prompt.kind == "instruction"

        outbox = AgentConfigOutbox.objects.order_by("-id").first()
        assert outbox.entity_type == "agent_prompt_version"
        assert outbox.payload["version"] == 1
        assert outbox.payload["body"] == "You are the development agent."
        assert outbox.payload["content_hash"]

    @pytest.mark.django_db
    def test_create_prompt_binding_records_latest_policy(self, api_key_client, workspace, create_user):
        agent_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-agents/",
            {
                "key": "codex-reviewer",
                "name": "Codex Reviewer",
                "runtime": "codex",
                "owner": str(create_user.id),
            },
            format="json",
        )
        prompt_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompts/",
            {
                "key": "review-rules",
                "name": "Review Rules",
                "scope": "role",
                "kind": "constraint",
            },
            format="json",
        )
        binding_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-bindings/",
            {
                "agent": agent_response.data["id"],
                "prompt": prompt_response.data["id"],
                "target_type": "user_agent",
                "version_policy": "latest",
                "slot": "role",
                "sort_order": 10,
            },
            format="json",
        )

        assert binding_response.status_code == status.HTTP_201_CREATED, (
            f"Got {binding_response.status_code}: {binding_response.data!r}"
        )

        binding = AgentPromptBinding.objects.get(id=binding_response.data["id"])
        assert binding.target_id == str(binding.agent_id)
        assert binding.version_policy == "latest"

        outbox = AgentConfigOutbox.objects.order_by("-id").first()
        assert outbox.entity_type == "agent_prompt_binding"
        assert outbox.payload["target_type"] == "user_agent"
        assert outbox.payload["target_id"] == str(binding.agent_id)
        assert outbox.payload["version_policy"] == "latest"
        assert outbox.payload["slot"] == "role"

    @pytest.mark.django_db
    def test_create_user_secret_key_writes_key_only_outbox(self, api_key_client, workspace, create_user):
        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-user-secret-keys/",
            {
                "owner": str(create_user.id),
                "key": "github-token",
                "description": "GitHub access token key",
                "provider": "env",
                "provider_ref": "GITHUB_TOKEN",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Got {response.status_code}: {response.data!r}"

        outbox = AgentConfigOutbox.objects.order_by("-id").first()
        assert outbox.entity_type == "agent_user_secret_key"
        assert outbox.payload["key"] == "github-token"
        assert outbox.payload["provider_ref"] == "GITHUB_TOKEN"
        assert "value" not in outbox.payload
