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
    AgentProjectDefault,
    AgentRepository,
    AgentTaskContextDocument,
    AgentTaskContextDocumentVersion,
    AgentTaskProgressEntry,
    AgentTaskWorkflowInstance,
    AgentTaskWorkflowNode,
    AgentTaskWorkflowTransition,
    AgentTaskWorkDirectoryOverride,
    AgentUserAgent,
    AgentWorkDirectory,
    AgentWorkDirectoryRepository,
    AgentWorkerCard,
    AgentWorkerMount,
    Issue,
    IssueComment,
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
    def test_register_multi_repo_work_directory_and_worker_mount(self, api_key_client, workspace, create_user):
        worker_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-worker-cards/",
            {
                "key": "mac-studio",
                "name": "Mac Studio Worker",
                "worker_endpoint": "http://80.251.222.30:3112",
                "capabilities": ["shell", "git", "docker"],
            },
            format="json",
        )
        assert worker_response.status_code == status.HTTP_201_CREATED, worker_response.data

        work_directory_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directories/",
            {
                "key": "agent-platform",
                "name": "Agent Platform",
                "root_path": "/Users/a/aiworkspace/agent-platform",
                "default_worker_card": worker_response.data["id"],
                "worktree_strategy": "per_task",
            },
            format="json",
        )
        assert work_directory_response.status_code == status.HTTP_201_CREATED, work_directory_response.data

        plane_repository = AgentRepository.objects.create(
            workspace=workspace,
            key="plane",
            provider="github",
            scm_provider="github",
            owner="michaelx1993",
            name="plane",
            full_name="michaelx1993/plane",
            url="https://github.com/michaelx1993/plane",
            clone_url="git@github.com:michaelx1993/plane.git",
            default_branch="preview",
        )
        acp_repository = AgentRepository.objects.create(
            workspace=workspace,
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

        first_link_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directory-repositories/",
            {
                "work_directory": work_directory_response.data["id"],
                "repository": str(plane_repository.id),
                "relative_path": "./plane",
                "sort_order": 10,
            },
            format="json",
        )
        second_link_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directory-repositories/",
            {
                "work_directory": work_directory_response.data["id"],
                "repository": str(acp_repository.id),
                "relative_path": "./agent-control-plane",
                "sort_order": 20,
            },
            format="json",
        )
        mount_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-worker-mounts/",
            {
                "work_directory": work_directory_response.data["id"],
                "worker_card": worker_response.data["id"],
                "local_path": "/Users/a/aiworkspace/agent-platform",
                "is_default": True,
            },
            format="json",
        )

        assert first_link_response.status_code == status.HTTP_201_CREATED, first_link_response.data
        assert second_link_response.status_code == status.HTTP_201_CREATED, second_link_response.data
        assert mount_response.status_code == status.HTTP_201_CREATED, mount_response.data
        assert first_link_response.data["default_branch"] == "preview"
        assert second_link_response.data["repository_key"] == "agent-control-plane"

        detail_response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directories/{work_directory_response.data['id']}/"
        )
        assert detail_response.status_code == status.HTTP_200_OK, detail_response.data
        assert detail_response.data["repository_count"] == 2
        assert detail_response.data["mount_count"] == 1
        assert detail_response.data["default_worker_key"] == "mac-studio"

        outbox = AgentConfigOutbox.objects.order_by("-id").first()
        assert outbox.entity_type == "agent_worker_mount"
        assert outbox.payload["local_path"] == "/Users/a/aiworkspace/agent-platform"

    @pytest.mark.django_db
    def test_project_default_and_task_override_resolve_work_directory(
        self,
        api_key_client,
        workspace,
        create_user,
    ):
        project = Project.objects.create(
            name="Runtime Project",
            identifier="RUN",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(
            name="Build work directory context",
            workspace=workspace,
            project=project,
            sequence_id=8,
        )
        mac_worker = AgentWorkerCard.objects.create(workspace=workspace, key="mac-studio", name="Mac Studio")
        mbp_worker = AgentWorkerCard.objects.create(workspace=workspace, key="mbp", name="MBP")
        default_directory = AgentWorkDirectory.objects.create(
            workspace=workspace,
            key="default-stack",
            name="Default Stack",
            root_path="/Users/a/aiworkspace/default-stack",
            default_worker_card=mac_worker,
        )
        override_directory = AgentWorkDirectory.objects.create(
            workspace=workspace,
            key="hotfix-stack",
            name="Hotfix Stack",
            root_path="/Users/a/aiworkspace/hotfix-stack",
            default_worker_card=mbp_worker,
        )
        repository = AgentRepository.objects.create(
            workspace=workspace,
            key="plane",
            provider="github",
            scm_provider="github",
            owner="michaelx1993",
            name="plane",
            full_name="michaelx1993/plane",
            url="https://github.com/michaelx1993/plane",
            clone_url="git@github.com:michaelx1993/plane.git",
            default_branch="preview",
        )
        AgentWorkDirectoryRepository.objects.create(
            workspace=workspace,
            work_directory=default_directory,
            repository=repository,
            relative_path="./plane",
        )
        AgentWorkerMount.objects.create(
            workspace=workspace,
            work_directory=default_directory,
            worker_card=mac_worker,
            local_path="/Users/a/aiworkspace/default-stack",
        )
        AgentWorkerMount.objects.create(
            workspace=workspace,
            work_directory=override_directory,
            worker_card=mbp_worker,
            local_path="/Users/a/work/hotfix-stack",
        )

        project_default_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-project-defaults/",
            {
                "project": str(project.id),
                "work_directory": str(default_directory.id),
                "worker_card": str(mac_worker.id),
            },
            format="json",
        )
        assert project_default_response.status_code == status.HTTP_201_CREATED, project_default_response.data

        project_resolution = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directory-resolution/"
            f"?project_id={project.id}&worker_id={mac_worker.id}"
        )
        assert project_resolution.status_code == status.HTTP_200_OK, project_resolution.data
        assert project_resolution.data["source"] == "project_default"
        assert project_resolution.data["workDirectory"]["key"] == "default-stack"
        assert project_resolution.data["worker"]["key"] == "mac-studio"
        assert project_resolution.data["mount"]["localPath"] == "/Users/a/aiworkspace/default-stack"
        assert project_resolution.data["repositories"][0]["relativePath"] == "./plane"

        override_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-work-directory-overrides/",
            {
                "issue": str(issue.id),
                "work_directory": str(override_directory.id),
                "worker_card": str(mbp_worker.id),
                "target_branch": "hotfix/agent-runtime",
            },
            format="json",
        )
        assert override_response.status_code == status.HTTP_201_CREATED, override_response.data

        task_resolution = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-work-directory-resolution/"
            f"?project_id={project.id}&work_item_id={issue.id}"
        )
        assert task_resolution.status_code == status.HTTP_200_OK, task_resolution.data
        assert task_resolution.data["source"] == "task_override"
        assert task_resolution.data["workDirectory"]["key"] == "hotfix-stack"
        assert task_resolution.data["worker"]["key"] == "mbp"
        assert task_resolution.data["mount"]["localPath"] == "/Users/a/work/hotfix-stack"

        assert AgentProjectDefault.objects.get(project=project).work_directory == default_directory
        assert AgentTaskWorkDirectoryOverride.objects.get(issue=issue).work_directory == override_directory

    @pytest.mark.django_db
    def test_agent_run_intent_includes_resolved_work_directory_context(
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
            name="Dispatch with work directory",
            workspace=workspace,
            project=project,
            sequence_id=9,
        )
        agent = AgentUserAgent.objects.create(
            workspace=workspace,
            owner=create_user,
            key="codex-default",
            name="Codex Default",
            runtime="codex",
        )
        worker = AgentWorkerCard.objects.create(workspace=workspace, key="mac-studio", name="Mac Studio")
        work_directory = AgentWorkDirectory.objects.create(
            workspace=workspace,
            key="agent-platform",
            name="Agent Platform",
            root_path="/Users/a/aiworkspace/agent-platform",
            default_worker_card=worker,
            branch_policy={"default_target": "preview"},
        )
        repository = AgentRepository.objects.create(
            workspace=workspace,
            key="plane",
            provider="github",
            scm_provider="github",
            owner="michaelx1993",
            name="plane",
            full_name="michaelx1993/plane",
            url="https://github.com/michaelx1993/plane",
            clone_url="git@github.com:michaelx1993/plane.git",
            default_branch="preview",
        )
        AgentWorkDirectoryRepository.objects.create(
            workspace=workspace,
            work_directory=work_directory,
            repository=repository,
            relative_path="./plane",
        )
        AgentWorkerMount.objects.create(
            workspace=workspace,
            work_directory=work_directory,
            worker_card=worker,
            local_path="/Users/a/aiworkspace/agent-platform",
        )
        AgentProjectDefault.objects.create(
            workspace=workspace,
            project=project,
            work_directory=work_directory,
            worker_card=worker,
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
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert posted["json"]["workerKey"] == "mac-studio"
        assert posted["json"]["workDirectory"]["source"] == "project_default"
        assert posted["json"]["workDirectory"]["workDirectory"]["key"] == "agent-platform"
        assert posted["json"]["workDirectory"]["workDirectory"]["branchPolicy"] == {"default_target": "preview"}
        assert posted["json"]["workDirectory"]["worker"]["key"] == "mac-studio"
        assert posted["json"]["workDirectory"]["mount"]["localPath"] == "/Users/a/aiworkspace/agent-platform"
        assert posted["json"]["workDirectory"]["repositories"] == [
            {
                "id": str(repository.id),
                "key": "plane",
                "provider": "github",
                "name": "plane",
                "fullName": "michaelx1993/plane",
                "url": "git@github.com:michaelx1993/plane.git",
                "relativePath": "./plane",
                "defaultBranch": "preview",
                "worktreeStrategy": "per_run",
                "isRequired": True,
            }
        ]

    @pytest.mark.django_db
    def test_task_context_documents_version_and_progress_entries(
        self,
        api_key_client,
        workspace,
        create_user,
    ):
        project = Project.objects.create(
            name="Context Project",
            identifier="CTX",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(
            name="Write task PRD",
            workspace=workspace,
            project=project,
        )

        prd_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-documents/",
            {
                "issue": str(issue.id),
                "document_type": "prd",
                "title": "prd.md",
                "body": "# PRD\n\nBuild the task context API.",
            },
            format="json",
        )
        status_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-documents/",
            {
                "issue": str(issue.id),
                "document_type": "status",
                "title": "status.md",
                "body": "# Status\n\nIntake.",
            },
            format="json",
        )

        assert prd_response.status_code == status.HTTP_201_CREATED, prd_response.data
        assert status_response.status_code == status.HTTP_201_CREATED, status_response.data
        assert prd_response.data["path"] == "prd.md"
        assert prd_response.data["version"] == 1

        duplicate_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-documents/",
            {
                "issue": str(issue.id),
                "document_type": "prd",
                "body": "duplicate",
            },
            format="json",
        )
        assert duplicate_response.status_code == status.HTTP_400_BAD_REQUEST

        update_response = api_key_client.patch(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-documents/{prd_response.data['id']}/",
            {"body": "# PRD\n\nBuild the task context API with tests."},
            format="json",
        )
        assert update_response.status_code == status.HTTP_200_OK, update_response.data
        assert update_response.data["version"] == 2

        versions_response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-document-versions/"
            f"?document_id={prd_response.data['id']}"
        )
        assert versions_response.status_code == status.HTTP_200_OK, versions_response.data
        assert [item["version"] for item in versions_response.data["results"]] == [2, 1]
        assert AgentTaskContextDocument.objects.get(id=prd_response.data["id"]).version == 2
        assert AgentTaskContextDocumentVersion.objects.filter(document_id=prd_response.data["id"]).count() == 2
        assert AgentTaskProgressEntry.objects.filter(issue=issue, source="system").count() == 3

    @pytest.mark.django_db
    def test_task_progress_entries_are_append_only_api(
        self,
        api_key_client,
        workspace,
        create_user,
    ):
        project = Project.objects.create(
            name="Progress Project",
            identifier="PRG",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(
            name="Append progress",
            workspace=workspace,
            project=project,
        )

        response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-progress-entries/",
            {
                "issue": str(issue.id),
                "entry_type": "validation",
                "source": "agent",
                "body": "Ran contract tests.",
                "summary": "Tests passed",
                "node_key": "development",
                "run_id": "run-1",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["body"] == "Ran contract tests."
        assert response.data["entry_type"] == "validation"

        list_response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-progress-entries/?issue_id={issue.id}"
        )
        assert list_response.status_code == status.HTTP_200_OK, list_response.data
        assert list_response.data["results"][0]["run_id"] == "run-1"

        patch_response = api_key_client.patch(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-progress-entries/{response.data['id']}/",
            {"body": "mutated"},
            format="json",
        )
        assert patch_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_task_context_snapshot_returns_documents_progress_comments_and_work_directory(
        self,
        api_key_client,
        workspace,
        create_user,
    ):
        project = Project.objects.create(
            name="Snapshot Project",
            identifier="SNP",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(
            name="Render agent context",
            workspace=workspace,
            project=project,
        )
        worker = AgentWorkerCard.objects.create(workspace=workspace, key="mac-studio", name="Mac Studio")
        work_directory = AgentWorkDirectory.objects.create(
            workspace=workspace,
            key="agent-platform",
            name="Agent Platform",
            root_path="/Users/a/aiworkspace/agent-platform",
            default_worker_card=worker,
        )
        repository = AgentRepository.objects.create(
            workspace=workspace,
            key="plane",
            provider="github",
            scm_provider="github",
            owner="michaelx1993",
            name="plane",
            full_name="michaelx1993/plane",
            url="https://github.com/michaelx1993/plane",
            clone_url="git@github.com:michaelx1993/plane.git",
            default_branch="preview",
        )
        AgentWorkDirectoryRepository.objects.create(
            workspace=workspace,
            work_directory=work_directory,
            repository=repository,
            relative_path="./plane",
        )
        AgentWorkerMount.objects.create(
            workspace=workspace,
            work_directory=work_directory,
            worker_card=worker,
            local_path="/Users/a/aiworkspace/agent-platform",
        )
        AgentProjectDefault.objects.create(
            workspace=workspace,
            project=project,
            work_directory=work_directory,
            worker_card=worker,
        )
        AgentTaskContextDocument.objects.create(
            workspace=workspace,
            issue=issue,
            document_type="prd",
            title="prd.md",
            body="# PRD\n\nBuild snapshot.",
        )
        AgentTaskContextDocument.objects.create(
            workspace=workspace,
            issue=issue,
            document_type="status",
            title="status.md",
            body="# Status\n\nReady.",
        )
        AgentTaskProgressEntry.objects.create(
            workspace=workspace,
            issue=issue,
            entry_type="progress",
            source="agent",
            body="Implemented snapshot serializer.",
            run_id="run-ctx",
        )
        IssueComment.objects.create(
            workspace=workspace,
            project=project,
            issue=issue,
            actor=create_user,
            comment_html="<p>Use the Plane DB as source of truth.</p>",
            created_by=create_user,
            updated_by=create_user,
        )

        response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-context-snapshot/"
            f"?project_id={project.id}&work_item_id={issue.id}"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["task"]["identifier"] == f"{project.identifier}-{issue.sequence_id}"
        assert response.data["documents"]["prd"]["body"] == "# PRD\n\nBuild snapshot."
        assert response.data["documents"]["status"]["path"] == "status.md"
        assert response.data["progressEntries"][0]["run_id"] == "run-ctx"
        assert "Implemented snapshot serializer." in response.data["renderedProgress"]
        assert response.data["humanComments"][0]["body"] == "Use the Plane DB as source of truth."
        assert response.data["workDirectory"]["workDirectory"]["key"] == "agent-platform"
        assert response.data["workDirectory"]["repositories"][0]["relativePath"] == "./plane"

    @pytest.mark.django_db
    def test_new_issue_auto_creates_default_workflow_instance(self, api_key_client, workspace, create_user):
        project = Project.objects.create(
            name="Workflow Project",
            identifier="WF",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)

        issue = Issue.objects.create(name="Build workflow API", workspace=workspace, project=project)

        workflow = AgentTaskWorkflowInstance.objects.get(issue=issue)
        assert workflow.template_key == "agent-software-delivery"
        assert workflow.active_node.key == "intake"
        assert workflow.status == "active"
        assert AgentTaskWorkflowNode.objects.filter(workflow_instance=workflow).count() == 12
        assert list(workflow.nodes.filter(status="active").values_list("key", flat=True)) == ["intake"]
        assert issue.state.name == "To-do / Intake / PRD"

        response = api_key_client.get(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-workflow-instances/?issue_id={issue.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["active_node_key"] == "intake"
        assert [node["key"] for node in response.data["results"][0]["nodes"]][:3] == [
            "intake",
            "development",
            "agent_review",
        ]

    @pytest.mark.django_db
    def test_workflow_actions_approve_and_set_auto(self, api_key_client, workspace, create_user):
        project = Project.objects.create(
            name="Gate Project",
            identifier="GATE",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(name="Review release gate", workspace=workspace, project=project)
        workflow = AgentTaskWorkflowInstance.objects.get(issue=issue)
        merged_gate = workflow.nodes.get(key="merged_gate")

        auto_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-workflow-actions/",
            {
                "workflow_instance": str(workflow.id),
                "node_key": "merged_gate",
                "action": "set_auto",
                "reason": "Trusted release path",
            },
            format="json",
        )

        assert auto_response.status_code == status.HTTP_200_OK, auto_response.data
        merged_gate.refresh_from_db()
        assert merged_gate.mode == "auto"
        assert auto_response.data["transition"]["action"] == "set_auto"

        approve_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-workflow-actions/",
            {
                "workflow_instance": str(workflow.id),
                "action": "approve",
            },
            format="json",
        )

        assert approve_response.status_code == status.HTTP_200_OK, approve_response.data
        workflow.refresh_from_db()
        assert workflow.active_node.key == "development"
        assert workflow.status == "active"
        assert workflow.nodes.get(key="intake").status == "completed"
        assert workflow.nodes.get(key="development").status == "active"
        assert AgentTaskWorkflowTransition.objects.filter(workflow_instance=workflow, action="approve").exists()
        assert AgentTaskProgressEntry.objects.filter(issue=issue, body__icontains="Approved").exists()

    @pytest.mark.django_db
    def test_agent_failed_blocks_then_human_returns_to_development(self, api_key_client, workspace, create_user):
        project = Project.objects.create(
            name="Blocked Project",
            identifier="BLK",
            workspace=workspace,
            created_by=create_user,
            updated_by=create_user,
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20)
        issue = Issue.objects.create(name="Handle failed run", workspace=workspace, project=project)
        workflow = AgentTaskWorkflowInstance.objects.get(issue=issue)
        workflow.active_node.status = "pending"
        workflow.active_node.save(update_fields=["status"])
        development = workflow.nodes.get(key="development")
        development.status = "active"
        development.save(update_fields=["status"])
        workflow.active_node = development
        workflow.save(update_fields=["active_node"])

        failed_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-workflow-actions/",
            {
                "issue": str(issue.id),
                "action": "agent_failed",
                "reason": "Tests failed",
            },
            format="json",
        )

        assert failed_response.status_code == status.HTTP_200_OK, failed_response.data
        workflow.refresh_from_db()
        assert workflow.status == "blocked"
        assert workflow.active_node.key == "blocked"
        assert workflow.nodes.get(key="development").status == "failed"

        return_response = api_key_client.post(
            f"/api/v1/workspaces/{workspace.slug}/agent-task-workflow-actions/",
            {
                "workflow_instance": str(workflow.id),
                "action": "return",
                "target_node_key": "development",
                "reason": "Added correction in progress.",
            },
            format="json",
        )

        assert return_response.status_code == status.HTTP_200_OK, return_response.data
        workflow.refresh_from_db()
        assert workflow.status == "active"
        assert workflow.active_node.key == "development"
        assert workflow.nodes.get(key="blocked").status == "completed"
        assert AgentTaskWorkflowTransition.objects.filter(workflow_instance=workflow, action="return").exists()
        assert AgentTaskProgressEntry.objects.filter(issue=issue, body__icontains="Returned workflow").exists()

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
