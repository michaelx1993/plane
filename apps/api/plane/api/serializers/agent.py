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
    AgentWorkerCard,
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
            "visibility",
            "latest_version",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "latest_version", "created_at", "updated_at"]


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
        for field_name in ["prompt_version", "role"]:
            instance = attrs.get(field_name)
            if instance is not None and str(instance.workspace_id) != str(workspace_id):
                raise serializers.ValidationError({field_name: "Object must belong to the current workspace."})
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
            "local_path",
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
            "name",
            "url",
            "default_branch",
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
