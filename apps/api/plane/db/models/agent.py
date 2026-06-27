# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import hashlib
import json

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

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

TASK_CONTEXT_DOCUMENT_TYPE_CHOICES = (
    ("prd", "PRD"),
    ("status", "Status"),
)

TASK_CONTEXT_SOURCE_CHOICES = (
    ("human", "Human"),
    ("agent", "Agent"),
    ("system", "System"),
)

TASK_PROGRESS_ENTRY_TYPE_CHOICES = (
    ("progress", "Progress"),
    ("decision", "Decision"),
    ("evidence", "Evidence"),
    ("validation", "Validation"),
    ("handoff", "Handoff"),
    ("feedback", "Feedback"),
)

TASK_WORKFLOW_INSTANCE_STATUS_CHOICES = (
    ("active", "Active"),
    ("blocked", "Blocked"),
    ("done", "Done"),
    ("canceled", "Canceled"),
)

TASK_WORKFLOW_NODE_TYPE_CHOICES = (
    ("intake", "Intake"),
    ("agent", "Agent"),
    ("agent_review", "Agent Review"),
    ("human_review", "Human Review"),
    ("merge", "Merge"),
    ("human_gate", "Human Gate"),
    ("release", "Release"),
    ("deploy", "Deployment"),
    ("exception", "Exception"),
    ("terminal", "Terminal"),
)

TASK_WORKFLOW_NODE_MODE_CHOICES = (
    ("manual", "Manual"),
    ("auto", "Auto"),
    ("conversational", "Conversational"),
    ("terminal", "Terminal"),
)

TASK_WORKFLOW_NODE_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("active", "Active"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("blocked", "Blocked"),
    ("skipped", "Skipped"),
)

TASK_WORKFLOW_TRANSITION_ACTION_CHOICES = (
    ("created", "Created"),
    ("approve", "Approve"),
    ("return", "Return"),
    ("set_auto", "Set Auto"),
    ("set_manual", "Set Manual"),
    ("block", "Block"),
    ("agent_failed", "Agent Failed"),
)

DEFAULT_TASK_WORKFLOW_TEMPLATE_KEY = "agent-software-delivery"
DEFAULT_TASK_WORKFLOW_TEMPLATE_VERSION = 1

DEFAULT_TASK_WORKFLOW_NODES = (
    {
        "key": "intake",
        "name": "To-do / Intake / PRD",
        "node_type": "intake",
        "owner_type": "human_agent",
        "mode": "manual",
        "sort_order": 1000,
        "main_exits": ["development", "blocked", "done"],
    },
    {
        "key": "development",
        "name": "Development",
        "node_type": "agent",
        "owner_type": "agent",
        "mode": "auto",
        "sort_order": 2000,
        "main_exits": ["agent_review", "blocked"],
    },
    {
        "key": "agent_review",
        "name": "Code Review / Agent Review",
        "node_type": "agent_review",
        "owner_type": "agent",
        "mode": "auto",
        "sort_order": 3000,
        "main_exits": ["human_review", "development", "blocked"],
    },
    {
        "key": "human_review",
        "name": "Human Review",
        "node_type": "human_review",
        "owner_type": "human",
        "mode": "manual",
        "sort_order": 4000,
        "main_exits": ["merge", "development", "done", "blocked"],
    },
    {
        "key": "merge",
        "name": "In Merge",
        "node_type": "merge",
        "owner_type": "agent",
        "mode": "auto",
        "sort_order": 5000,
        "main_exits": ["merged_gate", "development", "blocked"],
    },
    {
        "key": "merged_gate",
        "name": "Merged Gate",
        "node_type": "human_gate",
        "owner_type": "human",
        "mode": "manual",
        "sort_order": 6000,
        "main_exits": ["release", "development", "done", "blocked"],
    },
    {
        "key": "release",
        "name": "Release Version",
        "node_type": "release",
        "owner_type": "agent",
        "mode": "auto",
        "sort_order": 7000,
        "main_exits": ["released_gate", "development", "blocked"],
    },
    {
        "key": "released_gate",
        "name": "Released Gate",
        "node_type": "human_gate",
        "owner_type": "human",
        "mode": "manual",
        "sort_order": 8000,
        "main_exits": ["deployment", "development", "done", "blocked"],
    },
    {
        "key": "deployment",
        "name": "Deployment",
        "node_type": "deploy",
        "owner_type": "agent",
        "mode": "auto",
        "sort_order": 9000,
        "main_exits": ["deployed_gate", "development", "blocked"],
    },
    {
        "key": "deployed_gate",
        "name": "Deployed Gate",
        "node_type": "human_gate",
        "owner_type": "human",
        "mode": "manual",
        "sort_order": 10000,
        "main_exits": ["done", "development", "blocked"],
    },
    {
        "key": "done",
        "name": "Done",
        "node_type": "terminal",
        "owner_type": "system",
        "mode": "terminal",
        "sort_order": 11000,
        "main_exits": [],
    },
    {
        "key": "blocked",
        "name": "Blocked",
        "node_type": "exception",
        "owner_type": "human",
        "mode": "manual",
        "sort_order": 90000,
        "main_exits": ["intake", "development", "human_review", "merged_gate", "released_gate", "deployed_gate"],
    },
)

DEFAULT_TASK_WORKFLOW_NODE_BY_KEY = {node["key"]: node for node in DEFAULT_TASK_WORKFLOW_NODES}


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


class AgentTaskContextDocument(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_context_documents",
    )
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_context_documents",
    )
    document_type = models.CharField(max_length=40, choices=TASK_CONTEXT_DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    body_format = models.CharField(max_length=40, default="markdown")
    version = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_task_context_documents"
        ordering = ("issue", "document_type")
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "document_type"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_task_context_document_unique_issue_type",
            )
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.issue.workspace
        if not self.title:
            self.title = f"{self.document_type}.md"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.document_type}@{self.version}"


class AgentTaskContextDocumentVersion(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_context_document_versions",
    )
    document = models.ForeignKey(
        "db.AgentTaskContextDocument",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_context_document_versions",
    )
    document_type = models.CharField(max_length=40, choices=TASK_CONTEXT_DOCUMENT_TYPE_CHOICES)
    version = models.PositiveIntegerField()
    body = models.TextField(blank=True)
    body_format = models.CharField(max_length=40, default="markdown")
    change_summary = models.TextField(blank=True)
    source = models.CharField(max_length=40, choices=TASK_CONTEXT_SOURCE_CHOICES, default="human")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "agent_task_context_document_versions"
        ordering = ("document", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_task_context_document_version_unique",
            )
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.document.workspace
        self.issue = self.document.issue
        self.document_type = self.document.document_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_id}@{self.version}"


class AgentTaskProgressEntry(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_progress_entries",
    )
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_progress_entries",
    )
    entry_type = models.CharField(max_length=40, choices=TASK_PROGRESS_ENTRY_TYPE_CHOICES, default="progress")
    source = models.CharField(max_length=40, choices=TASK_CONTEXT_SOURCE_CHOICES, default="human")
    body = models.TextField()
    summary = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="agent_task_progress_entries",
        null=True,
        blank=True,
    )
    node_key = models.CharField(max_length=120, blank=True)
    run_id = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_task_progress_entries"
        ordering = ("issue", "occurred_at", "created_at")
        indexes = [
            models.Index(fields=["workspace", "issue", "occurred_at"]),
            models.Index(fields=["workspace", "source"]),
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.issue.workspace
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.entry_type}:{self.occurred_at.isoformat()}"


class AgentTaskWorkflowInstance(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_workflow_instances",
    )
    issue = models.OneToOneField(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_workflow_instance",
    )
    template_key = models.SlugField(max_length=120, default=DEFAULT_TASK_WORKFLOW_TEMPLATE_KEY)
    template_version = models.PositiveIntegerField(default=DEFAULT_TASK_WORKFLOW_TEMPLATE_VERSION)
    name = models.CharField(max_length=255, default="Agent software delivery workflow")
    status = models.CharField(
        max_length=40,
        choices=TASK_WORKFLOW_INSTANCE_STATUS_CHOICES,
        default="active",
    )
    active_node = models.ForeignKey(
        "db.AgentTaskWorkflowNode",
        on_delete=models.SET_NULL,
        related_name="active_workflow_instances",
        null=True,
        blank=True,
    )
    default_agent = models.ForeignKey(
        "db.AgentUserAgent",
        on_delete=models.SET_NULL,
        related_name="default_task_workflows",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_task_workflow_instances"
        ordering = ("issue__sequence_id",)
        indexes = [
            models.Index(fields=["workspace", "status"]),
            models.Index(fields=["workspace", "active_node"]),
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.issue.workspace
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.template_key}@{self.template_version}"


class AgentTaskWorkflowNode(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_workflow_nodes",
    )
    workflow_instance = models.ForeignKey(
        "db.AgentTaskWorkflowInstance",
        on_delete=models.CASCADE,
        related_name="nodes",
    )
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_workflow_nodes",
    )
    key = models.SlugField(max_length=120)
    name = models.CharField(max_length=255)
    node_type = models.CharField(max_length=40, choices=TASK_WORKFLOW_NODE_TYPE_CHOICES)
    owner_type = models.CharField(max_length=40, default="agent")
    mode = models.CharField(max_length=40, choices=TASK_WORKFLOW_NODE_MODE_CHOICES, default="auto")
    status = models.CharField(max_length=40, choices=TASK_WORKFLOW_NODE_STATUS_CHOICES, default="pending")
    sort_order = models.PositiveIntegerField(default=0)
    main_exits = models.JSONField(default=list, blank=True)
    assigned_agent = models.ForeignKey(
        "db.AgentUserAgent",
        on_delete=models.SET_NULL,
        related_name="assigned_workflow_nodes",
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "agent_task_workflow_nodes"
        ordering = ("workflow_instance", "sort_order")
        constraints = [
            models.UniqueConstraint(
                fields=["workflow_instance", "key"],
                condition=models.Q(deleted_at__isnull=True),
                name="agent_task_workflow_node_unique_key_instance",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "issue", "status"]),
            models.Index(fields=["workspace", "key"]),
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.workflow_instance.workspace
        self.issue = self.workflow_instance.issue
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.key}:{self.status}"


class AgentTaskWorkflowTransition(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="agent_task_workflow_transitions",
    )
    workflow_instance = models.ForeignKey(
        "db.AgentTaskWorkflowInstance",
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="agent_workflow_transitions",
    )
    from_node = models.ForeignKey(
        "db.AgentTaskWorkflowNode",
        on_delete=models.SET_NULL,
        related_name="outgoing_transitions",
        null=True,
        blank=True,
    )
    to_node = models.ForeignKey(
        "db.AgentTaskWorkflowNode",
        on_delete=models.SET_NULL,
        related_name="incoming_transitions",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=40, choices=TASK_WORKFLOW_TRANSITION_ACTION_CHOICES)
    reason = models.TextField(blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="agent_task_workflow_transitions",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "agent_task_workflow_transitions"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["workspace", "issue", "created_at"]),
            models.Index(fields=["workspace", "action"]),
        ]

    def save(self, *args, **kwargs):
        self.workspace = self.workflow_instance.workspace
        self.issue = self.workflow_instance.issue
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id}:{self.action}:{self.created_at.isoformat()}"


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


def ensure_default_task_workflow_instance(issue, actor=None):
    if issue.is_draft or issue.archived_at is not None:
        return None

    with transaction.atomic():
        existing = (
            AgentTaskWorkflowInstance.objects.select_related("active_node")
            .filter(issue=issue, workspace=issue.workspace, is_active=True)
            .first()
        )
        if existing:
            return existing

        workflow = AgentTaskWorkflowInstance.objects.create(workspace=issue.workspace, issue=issue)
        nodes = {}
        for node_spec in DEFAULT_TASK_WORKFLOW_NODES:
            node = AgentTaskWorkflowNode.objects.create(
                workspace=issue.workspace,
                workflow_instance=workflow,
                issue=issue,
                key=node_spec["key"],
                name=node_spec["name"],
                node_type=node_spec["node_type"],
                owner_type=node_spec["owner_type"],
                mode=node_spec["mode"],
                status="active" if node_spec["key"] == "intake" else "pending",
                sort_order=node_spec["sort_order"],
                main_exits=node_spec["main_exits"],
                started_at=timezone.now() if node_spec["key"] == "intake" else None,
            )
            nodes[node.key] = node

        workflow.active_node = nodes["intake"]
        workflow.save(update_fields=["active_node", "updated_at"])
        _record_task_workflow_transition(
            workflow,
            None,
            nodes["intake"],
            "created",
            actor=actor,
            reason="Created default Agent software delivery workflow.",
        )
        _sync_issue_state_to_workflow_node(issue, nodes["intake"])
        _record_task_workflow_outbox(workflow.workspace, "agent_task_workflow_instance", "create", workflow)
        for node in nodes.values():
            _record_task_workflow_outbox(workflow.workspace, "agent_task_workflow_node", "create", node)
        return workflow


def _record_task_workflow_transition(workflow, from_node, to_node, action, actor=None, reason="", metadata=None):
    return AgentTaskWorkflowTransition.objects.create(
        workspace=workflow.workspace,
        workflow_instance=workflow,
        issue=workflow.issue,
        from_node=from_node,
        to_node=to_node,
        action=action,
        reason=reason,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        metadata=metadata or {},
    )


def _sync_issue_state_to_workflow_node(issue, node):
    if node is None:
        return

    from plane.db.models import State

    group = {
        "intake": "unstarted",
        "agent": "started",
        "agent_review": "started",
        "human_review": "started",
        "merge": "started",
        "human_gate": "started",
        "release": "started",
        "deploy": "started",
        "exception": "started",
        "terminal": "completed",
    }.get(node.node_type, "started")
    color = {
        "unstarted": "#60646C",
        "started": "#F59E0B",
        "completed": "#46A758",
    }.get(group, "#60646C")
    state = State.all_state_objects.filter(project=issue.project, name=node.name, deleted_at__isnull=True).first()
    if state is None:
        state = State.objects.create(
            workspace=issue.workspace,
            project=issue.project,
            name=node.name,
            color=color,
            group=group,
        )
    if issue.state_id != state.id:
        issue.state = state
        issue.save(update_fields=["state"])


def _record_task_workflow_outbox(workspace, entity_type, operation, instance):
    AgentConfigOutbox.objects.create(
        workspace=workspace,
        entity_type=entity_type,
        entity_id=instance.id,
        operation=operation,
        payload=_task_workflow_outbox_payload(instance),
    )


def _task_workflow_outbox_payload(instance):
    if isinstance(instance, AgentTaskWorkflowInstance):
        return {
            "id": str(instance.id),
            "workspace": str(instance.workspace_id),
            "issue": str(instance.issue_id),
            "template_key": instance.template_key,
            "template_version": instance.template_version,
            "status": instance.status,
            "active_node": str(instance.active_node_id) if instance.active_node_id else None,
            "default_agent": str(instance.default_agent_id) if instance.default_agent_id else None,
        }
    if isinstance(instance, AgentTaskWorkflowNode):
        return {
            "id": str(instance.id),
            "workspace": str(instance.workspace_id),
            "workflow_instance": str(instance.workflow_instance_id),
            "issue": str(instance.issue_id),
            "key": instance.key,
            "name": instance.name,
            "node_type": instance.node_type,
            "owner_type": instance.owner_type,
            "mode": instance.mode,
            "status": instance.status,
            "main_exits": instance.main_exits,
            "assigned_agent": str(instance.assigned_agent_id) if instance.assigned_agent_id else None,
        }
    if isinstance(instance, AgentTaskWorkflowTransition):
        return {
            "id": str(instance.id),
            "workspace": str(instance.workspace_id),
            "workflow_instance": str(instance.workflow_instance_id),
            "issue": str(instance.issue_id),
            "from_node": str(instance.from_node_id) if instance.from_node_id else None,
            "to_node": str(instance.to_node_id) if instance.to_node_id else None,
            "action": instance.action,
            "reason": instance.reason,
        }
    return {"id": str(instance.id)}


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
