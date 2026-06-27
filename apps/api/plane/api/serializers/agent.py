# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db.models import Max
from rest_framework import serializers

from plane.db.models import (
    AgentConfigOutbox,
    AgentPrompt,
    AgentPromptBinding,
    AgentPromptVersion,
    AgentProjectDefault,
    AgentProjectWorkspace,
    AgentRepository,
    AgentRole,
    AgentTaskWorkDirectoryOverride,
    AgentUserAgent,
    AgentUserSecretKey,
    AgentWorkDirectory,
    AgentWorkDirectoryRepository,
    AgentWorkerCard,
    AgentWorkerMount,
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
    prompt_count = serializers.SerializerMethodField(read_only=True)
    prompt_stack = serializers.SerializerMethodField(read_only=True)

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
            "prompt_count",
            "prompt_stack",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def get_prompt_count(self, obj):
        return obj.prompt_bindings.filter(is_active=True).count()

    def get_prompt_stack(self, obj):
        bindings = obj.prompt_bindings.filter(is_active=True).select_related(
            "prompt",
            "prompt_version",
            "pinned_version",
            "role",
        )
        return AgentPromptBindingStackSerializer(bindings, many=True).data


class AgentPromptSerializer(AgentWorkspaceScopedSerializer):
    bound_agents_count = serializers.SerializerMethodField(read_only=True)
    version_count = serializers.SerializerMethodField(read_only=True)

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
            "bound_agents_count",
            "version_count",
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

    def get_bound_agents_count(self, obj):
        return obj.agent_bindings.filter(is_active=True).values("agent_id").distinct().count()

    def get_version_count(self, obj):
        return obj.versions.filter(is_active=True).count()


class AgentPromptVersionSerializer(AgentWorkspaceScopedSerializer):
    version = serializers.IntegerField(required=False, min_value=1)

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
        validators = []

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "prompt")
        prompt = attrs.get("prompt") or getattr(self.instance, "prompt", None)
        version = attrs.get("version") or getattr(self.instance, "version", None)
        if prompt is not None and version is not None:
            queryset = AgentPromptVersion.objects.filter(prompt=prompt, version=version)
            if self.instance is not None:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"version": "A prompt version with this prompt and version already exists."}
                )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("version"):
            latest_version = (
                AgentPromptVersion.objects.filter(prompt=validated_data["prompt"]).aggregate(Max("version"))[
                    "version__max"
                ]
                or 0
            )
            validated_data["version"] = latest_version + 1
        return super().create(validated_data)


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
        if version_policy == "latest":
            attrs["prompt_version"] = None
            attrs["pinned_version"] = None
            return attrs
        if version_policy == "pinned" and pinned_version is None:
            raise serializers.ValidationError({"pinned_version": "Pinned bindings require a prompt version."})
        if pinned_version is not None:
            prompt = attrs.get("prompt") or getattr(self.instance, "prompt", None)
            if prompt is not None and pinned_version.prompt_id != prompt.id:
                raise serializers.ValidationError(
                    {"pinned_version": "Pinned prompt version must belong to the selected prompt."}
                )
            attrs["prompt_version"] = pinned_version
            attrs["pinned_version"] = pinned_version
        return attrs


class AgentPromptBindingStackSerializer(serializers.ModelSerializer):
    prompt_key = serializers.CharField(source="prompt.key", read_only=True)
    prompt_name = serializers.CharField(source="prompt.name", read_only=True)
    prompt_scope = serializers.CharField(source="prompt.scope", read_only=True)
    prompt_kind = serializers.CharField(source="prompt.kind", read_only=True)
    prompt_status = serializers.CharField(source="prompt.status", read_only=True)
    resolved_version = serializers.SerializerMethodField(read_only=True)
    role_key = serializers.CharField(source="role.key", read_only=True)

    class Meta:
        model = AgentPromptBinding
        fields = [
            "id",
            "prompt",
            "prompt_key",
            "prompt_name",
            "prompt_scope",
            "prompt_kind",
            "prompt_status",
            "target_type",
            "target_id",
            "version_policy",
            "pinned_version",
            "resolved_version",
            "role",
            "role_key",
            "slot",
            "sort_order",
            "is_required",
        ]
        read_only_fields = fields

    def get_resolved_version(self, obj):
        if obj.version_policy == "pinned" and obj.pinned_version_id:
            return obj.pinned_version.version
        return obj.prompt.latest_version


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


class AgentWorkDirectorySerializer(AgentWorkspaceScopedSerializer):
    repository_count = serializers.SerializerMethodField(read_only=True)
    mount_count = serializers.SerializerMethodField(read_only=True)
    default_worker_key = serializers.CharField(source="default_worker_card.key", read_only=True)

    class Meta:
        model = AgentWorkDirectory
        fields = [
            "id",
            "workspace",
            "key",
            "name",
            "description",
            "root_path",
            "default_worker_card",
            "default_worker_key",
            "worktree_strategy",
            "branch_policy",
            "prd_path",
            "status_path",
            "progress_path",
            "repository_count",
            "mount_count",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "default_worker_card")
        return attrs

    def get_repository_count(self, obj):
        return obj.repositories.filter(is_active=True).count()

    def get_mount_count(self, obj):
        return obj.worker_mounts.filter(is_active=True).count()


class AgentWorkDirectoryRepositorySerializer(AgentWorkspaceScopedSerializer):
    repository_key = serializers.CharField(source="repository.key", read_only=True)
    repository_name = serializers.CharField(source="repository.name", read_only=True)
    repository_url = serializers.CharField(source="repository.clone_url", read_only=True)

    class Meta:
        model = AgentWorkDirectoryRepository
        fields = [
            "id",
            "workspace",
            "work_directory",
            "repository",
            "repository_key",
            "repository_name",
            "repository_url",
            "relative_path",
            "default_branch",
            "worktree_strategy",
            "sort_order",
            "is_required",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]
        validators = []

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "work_directory", "repository")
        work_directory = attrs.get("work_directory") or getattr(self.instance, "work_directory", None)
        repository = attrs.get("repository") or getattr(self.instance, "repository", None)
        if work_directory is not None and repository is not None:
            queryset = AgentWorkDirectoryRepository.objects.filter(
                work_directory=work_directory,
                repository=repository,
            )
            if self.instance is not None:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"repository": "Repository is already registered in this work directory."}
                )
        return attrs


class AgentWorkerMountSerializer(AgentWorkspaceScopedSerializer):
    worker_key = serializers.CharField(source="worker_card.key", read_only=True)
    worker_name = serializers.CharField(source="worker_card.name", read_only=True)
    work_directory_key = serializers.CharField(source="work_directory.key", read_only=True)

    class Meta:
        model = AgentWorkerMount
        fields = [
            "id",
            "workspace",
            "work_directory",
            "work_directory_key",
            "worker_card",
            "worker_key",
            "worker_name",
            "local_path",
            "is_default",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]
        validators = []

    def validate(self, attrs):
        self._assert_same_workspace(attrs, "work_directory", "worker_card")
        work_directory = attrs.get("work_directory") or getattr(self.instance, "work_directory", None)
        worker_card = attrs.get("worker_card") or getattr(self.instance, "worker_card", None)
        if work_directory is not None and worker_card is not None:
            queryset = AgentWorkerMount.objects.filter(work_directory=work_directory, worker_card=worker_card)
            if self.instance is not None:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"worker_card": "Worker already has a mount for this work directory."}
                )
        return attrs


class AgentProjectDefaultSerializer(AgentWorkspaceScopedSerializer):
    project_identifier = serializers.CharField(source="project.identifier", read_only=True)
    work_directory_key = serializers.CharField(source="work_directory.key", read_only=True)
    worker_key = serializers.CharField(source="worker_card.key", read_only=True)

    class Meta:
        model = AgentProjectDefault
        fields = [
            "id",
            "workspace",
            "project",
            "project_identifier",
            "work_directory",
            "work_directory_key",
            "worker_card",
            "worker_key",
            "metadata",
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
        self._assert_same_workspace(attrs, "work_directory", "worker_card")
        return attrs


class AgentTaskWorkDirectoryOverrideSerializer(AgentWorkspaceScopedSerializer):
    issue_sequence_id = serializers.IntegerField(source="issue.sequence_id", read_only=True)
    work_directory_key = serializers.CharField(source="work_directory.key", read_only=True)
    worker_key = serializers.CharField(source="worker_card.key", read_only=True)

    class Meta:
        model = AgentTaskWorkDirectoryOverride
        fields = [
            "id",
            "workspace",
            "issue",
            "issue_sequence_id",
            "work_directory",
            "work_directory_key",
            "worker_card",
            "worker_key",
            "target_branch",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace_id = self.context.get("workspace_id")
        issue = attrs.get("issue")
        if issue is not None and str(issue.workspace_id) != str(workspace_id):
            raise serializers.ValidationError({"issue": "Issue must belong to the current workspace."})
        self._assert_same_workspace(attrs, "work_directory", "worker_card")
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
