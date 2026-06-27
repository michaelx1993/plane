# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from rest_framework import status

from plane.api.views.agent import _agent_run_workflow_state
from plane.db.models import (
    AgentConfigOutbox,
    AgentPrompt,
    AgentPromptBinding,
    AgentPromptVersion,
    AgentRepository,
    AgentUserAgent,
    AgentWorkerCard,
    Issue,
    Project,
    ProjectMember,
)


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
    def test_create_prompt_version_auto_increments_when_version_is_omitted(self, api_key_client, workspace):
        prompt_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompts/",
            {
                "key": "builder-base",
                "name": "Builder Base",
                "scope": "agent",
                "kind": "instruction",
            },
            format="json",
        )
        assert prompt_response.status_code == status.HTTP_201_CREATED

        first_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-versions/",
            {
                "prompt": prompt_response.data["id"],
                "body": "First version",
            },
            format="json",
        )
        second_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-versions/",
            {
                "prompt": prompt_response.data["id"],
                "body": "Second version",
            },
            format="json",
        )

        assert first_response.status_code == status.HTTP_201_CREATED, first_response.data
        assert second_response.status_code == status.HTTP_201_CREATED, second_response.data
        assert first_response.data["version"] == 1
        assert second_response.data["version"] == 2
        assert AgentPrompt.objects.get(id=prompt_response.data["id"]).latest_version == 2

    @pytest.mark.django_db
    def test_create_prompt_version_rejects_duplicate_version(self, api_key_client, workspace):
        prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="builder-base",
            name="Builder Base",
            scope="agent",
            kind="instruction",
        )
        AgentPromptVersion.objects.create(workspace=workspace, prompt=prompt, version=1, body="First version")

        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-versions/",
            {
                "prompt": str(prompt.id),
                "version": 1,
                "body": "Duplicate version",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "version" in response.data

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
    def test_agent_detail_returns_ordered_prompt_stack(self, api_key_client, workspace, create_user):
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-builder",
            name="Codex Builder",
            runtime="codex",
        )
        base_prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="agent-base",
            name="Agent Base",
            scope="agent",
            kind="instruction",
        )
        project_prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="project-context",
            name="Project Context",
            scope="project",
            kind="context",
        )
        pinned_version = AgentPromptVersion.objects.create(
            workspace=workspace,
            prompt=project_prompt,
            version=1,
            body="Use the project constraints.",
        )
        AgentPromptVersion.objects.create(
            workspace=workspace,
            prompt=base_prompt,
            version=3,
            body="Use the latest base prompt.",
        )
        AgentPromptBinding.objects.create(
            agent=agent,
            prompt=project_prompt,
            prompt_version=pinned_version,
            version_policy="pinned",
            slot="project",
            sort_order=20,
        )
        AgentPromptBinding.objects.create(
            agent=agent,
            prompt=base_prompt,
            version_policy="latest",
            slot="agent",
            sort_order=10,
        )

        response = api_key_client.get(f"/api/v1/workspaces/{workspace.slug}/agent-agents/{agent.id}/")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["prompt_count"] == 2
        assert [item["prompt_key"] for item in response.data["prompt_stack"]] == [
            "agent-base",
            "project-context",
        ]
        assert response.data["prompt_stack"][0]["resolved_version"] == 3
        assert response.data["prompt_stack"][1]["version_policy"] == "pinned"
        assert response.data["prompt_stack"][1]["resolved_version"] == 1

    @pytest.mark.django_db
    def test_prompt_response_includes_binding_and_version_counts(self, api_key_client, workspace, create_user):
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-default",
            name="Codex Default",
        )
        prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="review-rules",
            name="Review Rules",
            scope="role",
            kind="constraint",
        )
        AgentPromptVersion.objects.create(workspace=workspace, prompt=prompt, version=1, body="v1")
        AgentPromptVersion.objects.create(workspace=workspace, prompt=prompt, version=2, body="v2")
        AgentPromptBinding.objects.create(agent=agent, prompt=prompt, version_policy="latest", slot="role")

        response = api_key_client.get(f"/api/v1/workspaces/{workspace.slug}/agent-prompts/{prompt.id}/")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["bound_agents_count"] == 1
        assert response.data["version_count"] == 2

    @pytest.mark.django_db
    def test_prompt_binding_rejects_pinned_version_from_another_prompt(self, api_key_client, workspace, create_user):
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-default",
            name="Codex Default",
        )
        selected_prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="selected",
            name="Selected Prompt",
            scope="agent",
            kind="instruction",
        )
        other_prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="other",
            name="Other Prompt",
            scope="agent",
            kind="instruction",
        )
        other_version = AgentPromptVersion.objects.create(
            workspace=workspace,
            prompt=other_prompt,
            version=1,
            body="Wrong prompt body",
        )

        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-bindings/",
            {
                "agent": str(agent.id),
                "prompt": str(selected_prompt.id),
                "pinned_version": str(other_version.id),
                "version_policy": "pinned",
                "slot": "agent",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pinned_version" in response.data

    @pytest.mark.django_db
    def test_prompt_binding_latest_policy_clears_pinned_version(self, api_key_client, workspace, create_user):
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-default",
            name="Codex Default",
        )
        prompt = AgentPrompt.objects.create(
            workspace=workspace,
            key="base",
            name="Base Prompt",
            scope="agent",
            kind="instruction",
        )
        prompt_version = AgentPromptVersion.objects.create(
            workspace=workspace,
            prompt=prompt,
            version=1,
            body="Pinned body",
        )
        binding = AgentPromptBinding.objects.create(
            agent=agent,
            prompt=prompt,
            prompt_version=prompt_version,
            version_policy="pinned",
            slot="agent",
        )

        response = api_key_client.patch(
            f"/api/v1/workspaces/{workspace.slug}/agent-prompt-bindings/{binding.id}/",
            {"version_policy": "latest"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        binding.refresh_from_db()
        assert binding.version_policy == "latest"
        assert binding.prompt_version is None
        assert binding.pinned_version is None

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

    @pytest.mark.django_db
    def test_agent_run_intent_forwards_selected_runtime_context(
        self,
        api_key_client,
        workspace,
        create_user,
        monkeypatch,
    ):
        monkeypatch.setenv("AGENT_CONTROL_PLANE_URL", "http://control-plane.test")
        project = Project.objects.create(
            name="Runtime Project",
            identifier="RUN",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(
            name="Build dispatch context",
            workspace=workspace,
            project=project,
            sequence_id=7,
        )
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-default",
            name="Codex Default",
            runtime="codex",
            model="gpt-5-codex",
        )
        repository = AgentRepository.objects.create(
            workspace=workspace,
            project=project,
            key="agent-control-plane",
            provider="github",
            scm_provider="github",
            owner="michaelx1993",
            name="agent-control-plane",
            full_name="michaelx1993/agent-control-plane",
            url="https://github.com/michaelx1993/agent-control-plane",
            clone_url="git@github.com:michaelx1993/agent-control-plane.git",
            default_branch="main",
        )
        worker = AgentWorkerCard.objects.create(
            workspace=workspace,
            key="mac-studio-worker-1",
            name="Mac Studio Worker",
            worker_endpoint="http://80.251.222.30:3112",
        )
        posted = {}

        class FakeResponse:
            status_code = 200
            text = ""

            def json(self):
                return {"ok": True, "queued": True, "task": {"taskId": "task-1"}}

        def fake_post(url, json, headers, timeout):
            posted.update({"url": url, "json": json, "headers": headers, "timeout": timeout})
            return FakeResponse()

        monkeypatch.setattr("plane.api.views.agent.requests.post", fake_post)

        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-runs/",
            {
                "project_id": str(project.id),
                "work_item_id": str(issue.id),
                "agent_id": str(agent.id),
                "repository_id": str(repository.id),
                "worker_id": str(worker.id),
                "prompt_version_ids": ["prompt-version-1", ""],
                "available_secret_keys": ["GITHUB_TOKEN"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, f"Got {response.status_code}: {response.data!r}"
        assert posted["url"] == "http://control-plane.test/api/runs"
        identifier = f"{project.identifier}-{issue.sequence_id}"
        assert posted["json"] == {
            "source": "plane",
            "planeProjectId": str(project.id),
            "projectSlug": "run",
            "externalTaskId": str(issue.id),
            "identifier": identifier,
            "title": "Build dispatch context",
            "state": "Todo",
            "priority": 5,
            "url": f"http://testserver/{workspace.slug}/browse/{identifier}/",
            "agentId": str(agent.id),
            "agentKey": "codex-default",
            "agentName": "Codex Default",
            "agentRuntime": "codex",
            "agentModel": "gpt-5-codex",
            "repositoryId": str(repository.id),
            "repositoryKey": "agent-control-plane",
            "repositoryUrl": "git@github.com:michaelx1993/agent-control-plane.git",
            "workerCardId": str(worker.id),
            "workerKey": "mac-studio-worker-1",
            "workerName": "Mac Studio Worker",
            "workerEndpoint": "http://80.251.222.30:3112",
            "promptVersionIds": ["prompt-version-1"],
            "availableSecretKeys": ["GITHUB_TOKEN"],
        }
