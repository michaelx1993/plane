# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from rest_framework import status

from plane.db.models import AgentConfigOutbox, AgentPrompt


@pytest.mark.contract
class TestAgentConfigAPI:
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
                "prompt_type": "agent",
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

        outbox = AgentConfigOutbox.objects.order_by("-id").first()
        assert outbox.entity_type == "agent_prompt_version"
        assert outbox.payload["version"] == 1
        assert outbox.payload["body"] == "You are the development agent."
