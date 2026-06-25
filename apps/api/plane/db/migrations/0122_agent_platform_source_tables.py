# Generated for Agent Control Plane source configuration tables.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("db", "0121_alter_estimate_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentConfigOutbox",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("entity_type", models.CharField(max_length=80)),
                ("entity_id", models.UUIDField()),
                (
                    "operation",
                    models.CharField(
                        choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete")],
                        max_length=20,
                    ),
                ),
                ("projection_version", models.PositiveIntegerField(default=1)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_config_outbox",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_config_outbox",
                "ordering": ("id",),
            },
        ),
        migrations.CreateModel(
            name="AgentPrompt",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("key", models.SlugField(max_length=120)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "prompt_type",
                    models.CharField(
                        choices=[
                            ("agent", "Agent"),
                            ("project", "Project"),
                            ("role", "Role"),
                            ("playbook_task", "Playbook Task"),
                            ("business_system", "Business System"),
                        ],
                        max_length=40,
                    ),
                ),
                ("visibility", models.CharField(default="workspace", max_length=40)),
                ("latest_version", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_prompts",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_prompts",
                "ordering": ("prompt_type", "name"),
            },
        ),
        migrations.CreateModel(
            name="AgentUserAgent",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("key", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("runtime", models.CharField(default="codex", max_length=80)),
                ("model", models.CharField(blank=True, max_length=120)),
                ("tools", models.JSONField(blank=True, default=list)),
                ("defaults", models.JSONField(blank=True, default=dict)),
                ("is_default", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owned_agent_user_agents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_user_agents",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_user_agents",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="AgentWorkerCard",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("key", models.SlugField(max_length=120)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("worker_endpoint", models.CharField(blank=True, max_length=255)),
                ("capabilities", models.JSONField(blank=True, default=list)),
                ("labels", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_worker_cards",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_worker_cards",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="AgentPromptVersion",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("version", models.PositiveIntegerField()),
                ("body", models.TextField()),
                ("variables", models.JSONField(blank=True, default=list)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "prompt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="db.agentprompt",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_prompt_versions",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_prompt_versions",
                "ordering": ("prompt", "-version"),
            },
        ),
        migrations.CreateModel(
            name="AgentRole",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("key", models.SlugField(max_length=120)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "prompt",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="role_defaults",
                        to="db.agentprompt",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_roles",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_roles",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="AgentProjectWorkspace",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("local_path", models.CharField(max_length=512)),
                ("status_path", models.CharField(default="status.md", max_length=512)),
                ("progress_path", models.CharField(default="progress.md", max_length=512)),
                ("meta_path", models.CharField(default="meta.md", max_length=512)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_workspace",
                        to="db.project",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "worker_card",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="project_workspaces",
                        to="db.agentworkercard",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_project_workspaces",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_project_workspaces",
                "ordering": ("project__name",),
            },
        ),
        migrations.CreateModel(
            name="AgentPromptBinding",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("slot", models.CharField(default="agent", max_length=40)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_required", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "agent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prompt_bindings",
                        to="db.agentuseragent",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "prompt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_bindings",
                        to="db.agentprompt",
                    ),
                ),
                (
                    "prompt_version",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_bindings",
                        to="db.agentpromptversion",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="prompt_bindings",
                        to="db.agentrole",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_prompt_bindings",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_prompt_bindings",
                "ordering": ("agent", "sort_order", "created_at"),
            },
        ),
        migrations.CreateModel(
            name="AgentRepository",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("key", models.SlugField(max_length=120)),
                ("provider", models.CharField(default="github", max_length=40)),
                ("name", models.CharField(max_length=255)),
                ("url", models.CharField(max_length=512)),
                ("default_branch", models.CharField(default="default", max_length=255)),
                ("local_path", models.CharField(blank=True, max_length=512)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_required", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_repositories",
                        to="db.project",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_repositories",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_repositories",
                "ordering": ("name",),
            },
        ),
        migrations.AddIndex(
            model_name="agentconfigoutbox",
            index=models.Index(fields=["workspace", "id"], name="agent_confi_workspa_bd9499_idx"),
        ),
        migrations.AddIndex(
            model_name="agentconfigoutbox",
            index=models.Index(fields=["entity_type", "entity_id"], name="agent_confi_entity__f7f42a_idx"),
        ),
        migrations.AddConstraint(
            model_name="agentprompt",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "key"),
                name="agent_prompt_unique_key_workspace",
            ),
        ),
        migrations.AddConstraint(
            model_name="agentuseragent",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "key"),
                name="agent_user_agent_unique_key_workspace",
            ),
        ),
        migrations.AddConstraint(
            model_name="agentworkercard",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "key"),
                name="agent_worker_card_unique_key_workspace",
            ),
        ),
        migrations.AddConstraint(
            model_name="agentpromptversion",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("prompt", "version"),
                name="agent_prompt_version_unique_prompt_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="agentrole",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "key"),
                name="agent_role_unique_key_workspace",
            ),
        ),
        migrations.AddIndex(
            model_name="agentpromptbinding",
            index=models.Index(fields=["workspace", "agent", "is_active"], name="agent_promp_workspa_f0f9ae_idx"),
        ),
        migrations.AddConstraint(
            model_name="agentrepository",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "key"),
                name="agent_repository_unique_key_workspace",
            ),
        ),
    ]
