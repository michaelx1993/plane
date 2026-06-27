# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import hashlib
import json

from django.conf import settings
from django.db import models

from .base import BaseModel


PROMPT_SCOPE_CHOICES = (
    ("agent", "Agent"),
    ("project", "Project"),
    ("role", "Role"),
    ("playbook", "Playbook"),
    ("task", "Task"),
    ("workspace", "Workspace"),
)

PROMPT_TYPE_CHOICES = (
    ("agent", "Agent"),
    ("project", "Project"),
    ("role", "Role"),
    ("playbook", "Playbook"),
    ("playbook_task", "Playbook Task"),
    ("task", "Task"),
    ("workspace", "Workspace"),
    ("business_system", "Business System"),
)

PROMPT_KIND_CHOICES = (
    ("instruction", "Instruction"),
    ("context", "Context"),
    ("constraint", "Constraint"),
    ("workflow", "Workflow"),
    ("style", "Style"),
    ("safety", "Safety"),
    ("output_contract", "Output Contract"),
)

VERSION_POLICY_CHOICES = (
    ("latest", "Latest"),
    ("pinned", "Pinned"),
)

OUTBOX_OPERATION_CHOICES = (
    ("create", "Create"),
    ("update", "Update"),
    ("delete", "Delete"),
)


class AgentUserAgent(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_user_agents")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_agent_user_agents",
        null=True,
        blank=True,
    )
    key = models.SlugField(max_length=80)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    runtime = models.CharField(max_length=80, default="codex")
    model = models.CharField(max_length=120, blank=True)
    tools = models.JSONField(default=list, blank=True)
    defaults = models.JSONField(default=dict, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_user_agents"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_user_agent_unique_key_workspace",
            )
        ]

    def __str__(self):
        return self.name


class AgentPrompt(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_prompts")
    key = models.SlugField(max_length=120)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prompt_type = models.CharField(max_length=40, choices=PROMPT_TYPE_CHOICES)
    scope = models.CharField(max_length=40, choices=PROMPT_SCOPE_CHOICES, default="agent")
    kind = models.CharField(max_length=40, choices=PROMPT_KIND_CHOICES, default="instruction")
    visibility = models.CharField(max_length=40, default="workspace")
    status = models.CharField(max_length=40, default="active")
    latest_version = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_prompts"
        ordering = ("prompt_type", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_prompt_unique_key_workspace",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.scope:
            self.scope = prompt_type_to_scope(self.prompt_type)
        if not self.prompt_type:
            self.prompt_type = scope_to_prompt_type(self.scope)
        super().save(*args, **kwargs)


class AgentPromptVersion(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_prompt_versions")
    prompt = models.ForeignKey("db.AgentPrompt", on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    body = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    changelog = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_prompt_versions"
        ordering = ("prompt", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=["prompt", "version"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_prompt_version_unique_prompt_version",
            )
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.prompt.workspace
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                json.dumps(
                    {"body": self.body, "variables": self.variables},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        super().save(*args, **kwargs)
        if self.prompt.latest_version < self.version:
            self.prompt.latest_version = self.version
            self.prompt.save(update_fields=["latest_version"])

    def __str__(self):
        return f"{self.prompt.key}@{self.version}"


class AgentRole(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_roles")
    key = models.SlugField(max_length=120)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prompt = models.ForeignKey(
        "db.AgentPrompt",
        on_delete=models.SET_NULL,
        related_name="role_defaults",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_roles"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_role_unique_key_workspace",
            )
        ]

    def __str__(self):
        return self.name


class AgentPromptBinding(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_prompt_bindings")
    agent = models.ForeignKey("db.AgentUserAgent", on_delete=models.CASCADE, related_name="prompt_bindings")
    prompt = models.ForeignKey("db.AgentPrompt", on_delete=models.CASCADE, related_name="agent_bindings")
    prompt_version = models.ForeignKey(
        "db.AgentPromptVersion",
        on_delete=models.SET_NULL,
        related_name="agent_bindings",
        null=True,
        blank=True,
    )
    target_type = models.CharField(max_length=40, default="user_agent")
    target_id = models.CharField(max_length=80, blank=True)
    version_policy = models.CharField(max_length=20, choices=VERSION_POLICY_CHOICES, default="latest")
    pinned_version = models.ForeignKey(
        "db.AgentPromptVersion",
        on_delete=models.SET_NULL,
        related_name="pinned_agent_bindings",
        null=True,
        blank=True,
    )
    role = models.ForeignKey(
        "db.AgentRole",
        on_delete=models.SET_NULL,
        related_name="prompt_bindings",
        null=True,
        blank=True,
    )
    slot = models.CharField(max_length=40, default="agent")
    sort_order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_prompt_bindings"
        ordering = ("agent", "sort_order", "created_at")
        indexes = [
            models.Index(fields=["workspace", "agent", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.agent.workspace
        if not self.target_id:
            self.target_id = str(self.agent_id)
        if self.version_policy == "pinned" and self.pinned_version is None:
            self.pinned_version = self.prompt_version
        if self.version_policy == "latest":
            self.prompt_version = None
            self.pinned_version = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.agent.key}:{self.prompt.key}"


class AgentWorkerCard(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_worker_cards")
    key = models.SlugField(max_length=120)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    worker_endpoint = models.CharField(max_length=255, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    labels = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_worker_cards"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_worker_card_unique_key_workspace",
            )
        ]

    def __str__(self):
        return self.name


class AgentProjectWorkspace(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_project_workspaces")
    project = models.OneToOneField("db.Project", on_delete=models.CASCADE, related_name="agent_workspace")
    worker_card = models.ForeignKey(
        "db.AgentWorkerCard",
        on_delete=models.SET_NULL,
        related_name="project_workspaces",
        null=True,
        blank=True,
    )
    slug = models.SlugField(max_length=120, blank=True)
    name = models.CharField(max_length=255, blank=True)
    local_path = models.CharField(max_length=512)
    path_policy = models.CharField(max_length=80, default="worker_managed")
    meta_git_mode = models.CharField(max_length=80, default="local")
    meta_git_remote_url = models.CharField(max_length=512, blank=True)
    status_path = models.CharField(max_length=512, default="status.md")
    progress_path = models.CharField(max_length=512, default="progress.md")
    meta_path = models.CharField(max_length=512, default="meta.md")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_project_workspaces"
        ordering = ("project__name",)

    def save(self, *args, **kwargs):
        self.workspace = self.project.workspace
        if not self.slug:
            self.slug = self.project.identifier.lower()
        if not self.name:
            self.name = self.project.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.local_path


class AgentRepository(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_repositories")
    project = models.ForeignKey(
        "db.Project",
        on_delete=models.CASCADE,
        related_name="agent_repositories",
        null=True,
        blank=True,
    )
    key = models.SlugField(max_length=120)
    provider = models.CharField(max_length=40, default="github")
    scm_provider = models.CharField(max_length=40, default="github")
    owner = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=512, blank=True)
    url = models.CharField(max_length=512)
    clone_url = models.CharField(max_length=512, blank=True)
    default_branch = models.CharField(max_length=255, default="default")
    credential_key = models.CharField(max_length=255, blank=True)
    worktree_strategy = models.CharField(max_length=40, default="per_run")
    local_path = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_repositories"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_repository_unique_key_workspace",
            )
        ]

    def save(self, *args, **kwargs):
        if self.project:
            self.workspace = self.project.workspace
        if not self.scm_provider:
            self.scm_provider = self.provider
        if not self.clone_url:
            self.clone_url = self.url
        if not self.full_name:
            self.full_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AgentWorkDirectory(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_work_directories")
    key = models.SlugField(max_length=120)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    root_path = models.CharField(max_length=512, blank=True)
    default_worker_card = models.ForeignKey(
        "db.AgentWorkerCard",
        on_delete=models.SET_NULL,
        related_name="default_work_directories",
        null=True,
        blank=True,
    )
    worktree_strategy = models.CharField(max_length=40, default="per_task")
    branch_policy = models.JSONField(default=dict, blank=True)
    prd_path = models.CharField(max_length=512, default="prd.md")
    status_path = models.CharField(max_length=512, default="status.md")
    progress_path = models.CharField(max_length=512, default="progress.md")
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_work_directories"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_work_directory_unique_key_workspace",
            )
        ]

    def __str__(self):
        return self.name


class AgentWorkDirectoryRepository(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_work_directory_repositories",
    )
    work_directory = models.ForeignKey(
        "db.AgentWorkDirectory",
        on_delete=models.CASCADE,
        related_name="repositories",
    )
    repository = models.ForeignKey(
        "db.AgentRepository",
        on_delete=models.CASCADE,
        related_name="work_directory_links",
    )
    relative_path = models.CharField(max_length=512, default=".")
    default_branch = models.CharField(max_length=255, blank=True)
    worktree_strategy = models.CharField(max_length=40, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_work_directory_repositories"
        ordering = ("work_directory", "sort_order", "repository__name")
        constraints = [
            models.UniqueConstraint(
                fields=["work_directory", "repository"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_work_directory_repository_unique",
            )
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.work_directory.workspace
        if not self.default_branch:
            self.default_branch = self.repository.default_branch
        if not self.worktree_strategy:
            self.worktree_strategy = self.repository.worktree_strategy
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.work_directory.key}:{self.repository.key}"


class AgentWorkerMount(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_worker_mounts")
    work_directory = models.ForeignKey(
        "db.AgentWorkDirectory",
        on_delete=models.CASCADE,
        related_name="worker_mounts",
    )
    worker_card = models.ForeignKey(
        "db.AgentWorkerCard",
        on_delete=models.CASCADE,
        related_name="work_directory_mounts",
    )
    local_path = models.CharField(max_length=512)
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_worker_mounts"
        ordering = ("work_directory", "worker_card__name")
        constraints = [
            models.UniqueConstraint(
                fields=["work_directory", "worker_card"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_worker_mount_unique_directory_worker",
            )
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.work_directory.workspace
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker_card.key}:{self.local_path}"


class AgentProjectDefault(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_project_defaults")
    project = models.OneToOneField("db.Project", on_delete=models.CASCADE, related_name="agent_default")
    work_directory = models.ForeignKey(
        "db.AgentWorkDirectory",
        on_delete=models.SET_NULL,
        related_name="project_defaults",
        null=True,
        blank=True,
    )
    worker_card = models.ForeignKey(
        "db.AgentWorkerCard",
        on_delete=models.SET_NULL,
        related_name="project_defaults",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_project_defaults"
        ordering = ("project__name",)

    def save(self, *args, **kwargs):
        self.workspace = self.project.workspace
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.identifier}:{self.work_directory_id}"


class AgentTaskWorkDirectoryOverride(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_work_directory_overrides",
    )
    issue = models.OneToOneField("db.Issue", on_delete=models.CASCADE, related_name="agent_work_directory_override")
    work_directory = models.ForeignKey(
        "db.AgentWorkDirectory",
        on_delete=models.SET_NULL,
        related_name="task_overrides",
        null=True,
        blank=True,
    )
    worker_card = models.ForeignKey(
        "db.AgentWorkerCard",
        on_delete=models.SET_NULL,
        related_name="task_work_directory_overrides",
        null=True,
        blank=True,
    )
    target_branch = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_task_work_directory_overrides"
        ordering = ("issue__sequence_id",)

    def save(self, *args, **kwargs):
        self.workspace = self.issue.workspace
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.work_directory_id}"


class AgentConfigOutbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_config_outbox")
    entity_type = models.CharField(max_length=80)
    entity_id = models.UUIDField()
    operation = models.CharField(max_length=20, choices=OUTBOX_OPERATION_CHOICES)
    projection_version = models.PositiveIntegerField(default=1)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "agent_config_outbox"
        ordering = ("id",)
        indexes = [
            models.Index(fields=["workspace", "id"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.id}:{self.entity_type}:{self.operation}"


class AgentUserSecretKey(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_user_secret_keys")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_agent_user_secret_keys",
        null=True,
        blank=True,
    )
    key = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    provider = models.CharField(max_length=40, default="env")
    provider_ref = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=40, default="active")

    class Meta:
        db_table = "agent_user_secret_keys"
        ordering = ("key",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "owner", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_user_secret_key_unique_owner",
            )
        ]

    def __str__(self):
        return self.key


def prompt_type_to_scope(prompt_type):
    if prompt_type == "playbook_task":
        return "playbook"
    if prompt_type == "business_system":
        return "workspace"
    return prompt_type or "agent"


def scope_to_prompt_type(scope):
    if scope == "playbook":
        return "playbook_task"
    if scope == "workspace":
        return "business_system"
    return scope or "agent"
