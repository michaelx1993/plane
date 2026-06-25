# Align Agent Platform source tables with the Plane Agent Platform PRD.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_agent_platform_prd_fields(apps, schema_editor):
    AgentPrompt = apps.get_model("db", "AgentPrompt")
    AgentPrompt.objects.filter(prompt_type="playbook_task").update(scope="playbook")
    AgentPrompt.objects.filter(prompt_type="business_system").update(scope="workspace")
    AgentPrompt.objects.exclude(prompt_type__in=["playbook_task", "business_system"]).update(scope=models.F("prompt_type"))

    AgentPromptBinding = apps.get_model("db", "AgentPromptBinding")
    for binding in AgentPromptBinding.objects.all().only("id", "agent_id", "prompt_version_id"):
        binding.target_type = "user_agent"
        binding.target_id = str(binding.agent_id)
        if binding.prompt_version_id:
            binding.version_policy = "pinned"
            binding.pinned_version_id = binding.prompt_version_id
        binding.save(update_fields=["target_type", "target_id", "version_policy", "pinned_version"])

    AgentProjectWorkspace = apps.get_model("db", "AgentProjectWorkspace")
    for project_workspace in AgentProjectWorkspace.objects.select_related("project").all():
        if not project_workspace.slug:
            project_workspace.slug = project_workspace.project.identifier.lower()
        if not project_workspace.name:
            project_workspace.name = project_workspace.project.name
        project_workspace.save(update_fields=["slug", "name"])

    AgentRepository = apps.get_model("db", "AgentRepository")
    for repository in AgentRepository.objects.all().only("id", "provider", "name", "url", "scm_provider", "full_name", "clone_url"):
        if not repository.scm_provider:
            repository.scm_provider = repository.provider
        if not repository.full_name:
            repository.full_name = repository.name
        if not repository.clone_url:
            repository.clone_url = repository.url
        repository.save(update_fields=["scm_provider", "full_name", "clone_url"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("db", "0122_agent_platform_source_tables"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agentprompt",
            name="prompt_type",
            field=models.CharField(
                choices=[
                    ("agent", "Agent"),
                    ("project", "Project"),
                    ("role", "Role"),
                    ("playbook", "Playbook"),
                    ("playbook_task", "Playbook Task"),
                    ("task", "Task"),
                    ("workspace", "Workspace"),
                    ("business_system", "Business System"),
                ],
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="agentprompt",
            name="scope",
            field=models.CharField(
                choices=[
                    ("agent", "Agent"),
                    ("project", "Project"),
                    ("role", "Role"),
                    ("playbook", "Playbook"),
                    ("task", "Task"),
                    ("workspace", "Workspace"),
                ],
                default="agent",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="agentprompt",
            name="kind",
            field=models.CharField(
                choices=[
                    ("instruction", "Instruction"),
                    ("context", "Context"),
                    ("constraint", "Constraint"),
                    ("workflow", "Workflow"),
                    ("style", "Style"),
                    ("safety", "Safety"),
                    ("output_contract", "Output Contract"),
                ],
                default="instruction",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="agentprompt",
            name="status",
            field=models.CharField(default="active", max_length=40),
        ),
        migrations.AddField(
            model_name="agentpromptversion",
            name="content_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="agentpromptversion",
            name="changelog",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="agentpromptbinding",
            name="target_type",
            field=models.CharField(default="user_agent", max_length=40),
        ),
        migrations.AddField(
            model_name="agentpromptbinding",
            name="target_id",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="agentpromptbinding",
            name="version_policy",
            field=models.CharField(
                choices=[("latest", "Latest"), ("pinned", "Pinned")],
                default="latest",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="agentpromptbinding",
            name="pinned_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pinned_agent_bindings",
                to="db.agentpromptversion",
            ),
        ),
        migrations.AddField(
            model_name="agentprojectworkspace",
            name="slug",
            field=models.SlugField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="agentprojectworkspace",
            name="name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="agentprojectworkspace",
            name="path_policy",
            field=models.CharField(default="worker_managed", max_length=80),
        ),
        migrations.AddField(
            model_name="agentprojectworkspace",
            name="meta_git_mode",
            field=models.CharField(default="local", max_length=80),
        ),
        migrations.AddField(
            model_name="agentprojectworkspace",
            name="meta_git_remote_url",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="scm_provider",
            field=models.CharField(default="github", max_length=40),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="owner",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="full_name",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="clone_url",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="credential_key",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="agentrepository",
            name="worktree_strategy",
            field=models.CharField(default="per_run", max_length=40),
        ),
        migrations.CreateModel(
            name="AgentUserSecretKey",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("key", models.SlugField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("provider", models.CharField(default="env", max_length=40)),
                ("provider_ref", models.CharField(blank=True, max_length=512)),
                ("status", models.CharField(default="active", max_length=40)),
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
                        related_name="owned_agent_user_secret_keys",
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
                        related_name="agent_user_secret_keys",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "db_table": "agent_user_secret_keys",
                "ordering": ("key",),
            },
        ),
        migrations.AddConstraint(
            model_name="agentusersecretkey",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "owner", "key"),
                name="agent_user_secret_key_unique_owner",
            ),
        ),
        migrations.RunPython(backfill_agent_platform_prd_fields, noop_reverse),
    ]
