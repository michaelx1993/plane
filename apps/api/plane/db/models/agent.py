# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.conf import settings
from django.db import models

from .base import BaseModel


PROMPT_TYPE_CHOICES = (
    ("agent", "Agent"),
    ("project", "Project"),
    ("role", "Role"),
    ("playbook_task", "Playbook Task"),
    ("business_system", "Business System"),
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
    visibility = models.CharField(max_length=40, default="workspace")
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


class AgentPromptVersion(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="agent_prompt_versions")
    prompt = models.ForeignKey("db.AgentPrompt", on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    body = models.TextField()
    variables = models.JSONField(default=list, blank=True)
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
    local_path = models.CharField(max_length=512)
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
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=512)
    default_branch = models.CharField(max_length=255, default="default")
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
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
