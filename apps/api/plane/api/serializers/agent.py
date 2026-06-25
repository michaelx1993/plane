# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers

from plane.db.models import (
    AgentConfigOutbox,
    AgentPrompt,
    AgentPromptBinding,
    AgentPromptVersion,
    AgentProjectWorkspace,
    AgentRepository,
    AgentRole,
    AgentUserAgent,
    AgentUserSecretKey,
    AgentWorkerCard,
    prompt_type_to_scope,
    scope_to_prompt_type,
)

from .base import BaseSerializer


class AgentWorkspaceScopedSerializer(BaseSerializer):
    workspace = serializers.UUIDField(source="workspace_id", read_only=True)

    def _assert_same_workspace(self, attrs, *field_names):
        workspace_id = self.context.get("workspace_id")
        for field_name in field_names:
            instance = attrs.get(field_name)
            if instance is not None and str(instance.workspace_id) != str(workspace_id):
                raise serializers.ValidationError({field_name: "Object must belong to the current workspace."})


class AgentUserAgentSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentUserAgent
        fields = [
            "id",
            "workspace",
            "owner",
            "key",
            "name",
            "description",
            "runtime",
            "model",
            "tools",
            "defaults",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class AgentPromptSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentPrompt
        fields = [
            "id",
            "workspace",
            "key",
            "name",
            "description",
            "prompt_type",
            "scope",
            "kind",
            "visibility",
            "status",
            "latest_version",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "latest_version", "created_at", "updated_at"]
        extra_kwargs = {"prompt_type": {"required": False}}

    def validate(self, attrs):
        if not attrs.get("scope") and attrs.get("prompt_type"):
            attrs["scope"] = prompt_type_to_scope(attrs["prompt_type"])
        if not attrs.get("prompt_type") and attrs.get("scope"):
            attrs["prompt_type"] = scope_to_prompt_type(attrs["scope"])
        return attrs


class AgentPromptVersionSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentPromptVersion
        fields = [
            "id",
            "workspace",
            "prompt",
            "version",
            "body",
            "variables",
            "content_hash",
            "changelog",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "prompt")
        return attrs


class AgentRoleSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentRole
        fields = [
            "id",
            "workspace",
            "key",
            "name",
            "description",
            "prompt",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "prompt")
        return attrs


class AgentPromptBindingSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentPromptBinding
        fields = [
            "id",
            "workspace",
            "agent",
            "prompt",
            "prompt_version",
            "target_type",
            "target_id",
            "version_policy",
            "pinned_version",
            "role",
            "slot",
            "sort_order",
            "is_required",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "agent", "prompt")
        workspace_id = self.context.get("workspace_id")
        for field_name in ["prompt_version", "pinned_version", "role"]:
            instance = attrs.get(field_name)
            if instance is not None and str(instance.workspace_id) != str(workspace_id):
                raise serializers.ValidationError({field_name: "Object must belong to the current workspace."})
        version_policy = attrs.get("version_policy", getattr(self.instance, "version_policy", "latest"))
        pinned_version = (
            attrs.get("pinned_version")
            or attrs.get("prompt_version")
            or getattr(self.instance, "pinned_version", None)
        )
        if version_policy == "pinned" and pinned_version is None:
            raise serializers.ValidationError({"pinned_version": "Pinned bindings require a prompt version."})
        if pinned_version is not None:
            attrs["prompt_version"] = pinned_version
            attrs["pinned_version"] = pinned_version
        return attrs


class AgentWorkerCardSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentWorkerCard
        fields = [
            "id",
            "workspace",
            "key",
            "name",
            "description",
            "worker_endpoint",
            "capabilities",
            "labels",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class AgentProjectWorkspaceSerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentProjectWorkspace
        fields = [
            "id",
            "workspace",
            "project",
            "worker_card",
            "slug",
            "name",
            "local_path",
            "path_policy",
            "meta_git_mode",
            "meta_git_remote_url",
            "status_path",
            "progress_path",
            "meta_path",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace_id = self.context.get("workspace_id")
        project = attrs.get("project")
        worker_card = attrs.get("worker_card")
        if project is not None and str(project.workspace_id) != str(workspace_id):
            raise serializers.ValidationError({"project": "Project must belong to the current workspace."})
        if worker_card is not None and str(worker_card.workspace_id) != str(workspace_id):
            raise serializers.ValidationError({"worker_card": "Worker card must belong to the current workspace."})
        return attrs


class AgentRepositorySerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentRepository
        fields = [
            "id",
            "workspace",
            "project",
            "key",
            "provider",
            "scm_provider",
            "owner",
            "name",
            "full_name",
            "url",
            "clone_url",
            "default_branch",
            "credential_key",
            "worktree_strategy",
            "local_path",
            "metadata",
            "is_required",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace_id = self.context.get("workspace_id")
        project = attrs.get("project")
        if project is not None and str(project.workspace_id) != str(workspace_id):
            raise serializers.ValidationError({"project": "Project must belong to the current workspace."})
        return attrs


class AgentUserSecretKeySerializer(AgentWorkspaceScopedSerializer):
    class Meta:
        model = AgentUserSecretKey
        fields = [
            "id",
            "workspace",
            "owner",
            "key",
            "description",
            "provider",
            "provider_ref",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]


class AgentConfigOutboxSerializer(serializers.ModelSerializer):
    workspace = serializers.UUIDField(source="workspace_id", read_only=True)

    class Meta:
        model = AgentConfigOutbox
        fields = [
            "id",
            "workspace",
            "entity_type",
            "entity_id",
            "operation",
            "projection_version",
            "payload",
            "created_at",
        ]
        read_only_fields = fields
