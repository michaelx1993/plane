# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import os

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
import requests

from plane.api.middleware.api_authentication import APIKeyAuthentication
from plane.app.permissions import WorkspaceEntityPermission
from plane.authentication.session import BaseSessionAuthentication
from plane.api.serializers import (
    AgentConfigOutboxSerializer,
    AgentPromptBindingSerializer,
    AgentPromptSerializer,
    AgentPromptVersionSerializer,
    AgentProjectDefaultSerializer,
    AgentProjectWorkspaceSerializer,
    AgentRepositorySerializer,
    AgentRoleSerializer,
    AgentTaskContextDocumentSerializer,
    AgentTaskContextDocumentVersionSerializer,
    AgentTaskProgressEntrySerializer,
    AgentTaskWorkflowActionSerializer,
    AgentTaskWorkflowInstanceSerializer,
    AgentTaskWorkflowNodeSerializer,
    AgentTaskWorkflowTransitionSerializer,
    AgentTaskWorkDirectoryOverrideSerializer,
    AgentUserAgentSerializer,
    AgentUserSecretKeySerializer,
    AgentWorkDirectoryRepositorySerializer,
    AgentWorkDirectorySerializer,
    AgentWorkerCardSerializer,
    AgentWorkerMountSerializer,
)
from plane.db.models import (
    AgentConfigOutbox,
    AgentPrompt,
    AgentPromptBinding,
    AgentPromptVersion,
    AgentProjectDefault,
    AgentProjectWorkspace,
    AgentRepository,
    AgentRole,
    AgentTaskContextDocument,
    AgentTaskContextDocumentVersion,
    AgentTaskProgressEntry,
    AgentTaskWorkflowInstance,
    AgentTaskWorkflowNode,
    AgentTaskWorkflowTransition,
    AgentTaskWorkDirectoryOverride,
    AgentUserAgent,
    AgentUserSecretKey,
    AgentWorkDirectory,
    AgentWorkDirectoryRepository,
    AgentWorkerCard,
    AgentWorkerMount,
    Issue,
    Project,
    Workspace,
    ensure_default_task_workflow_instance,
)

from .base import BaseAPIView


def _record_agent_config_outbox(workspace, entity_type, operation, instance, serializer_class):
    payload = _json_payload(serializer_class(instance, context={"workspace_id": workspace.id}).data)
    return AgentConfigOutbox.objects.create(
        workspace=workspace,
        entity_type=entity_type,
        entity_id=instance.id,
        operation=operation,
        payload=payload,
    )


def _json_payload(payload):
    return json.loads(json.dumps(payload, cls=DjangoJSONEncoder))


class AgentConfigSourceListCreateAPIEndpoint(BaseAPIView):
    model = None
    serializer_class = None
    entity_type = None
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get_queryset(self):
        return self.model.objects.filter(workspace__slug=self.workspace_slug)

    def get_serializer_context(self):
        workspace = Workspace.objects.get(slug=self.workspace_slug)
        return {"workspace_id": workspace.id}

    def get(self, request, slug):
        queryset = self.get_queryset().order_by(request.GET.get("order_by", "-created_at"))
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda results: self.serializer_class(
                results,
                many=True,
                fields=self.fields,
                expand=self.expand,
                context=self.get_serializer_context(),
            ).data,
        )

    def post(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        serializer = self.serializer_class(data=request.data, context={"workspace_id": workspace.id})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save(workspace=workspace)
            _record_agent_config_outbox(workspace, self.entity_type, "create", instance, self.serializer_class)
        return Response(
            self.serializer_class(instance, context={"workspace_id": workspace.id}).data,
            status=status.HTTP_201_CREATED,
        )


class AgentConfigSourceDetailAPIEndpoint(BaseAPIView):
    model = None
    serializer_class = None
    entity_type = None
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get_queryset(self):
        return self.model.objects.filter(workspace__slug=self.workspace_slug)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

    def get_serializer_context(self):
        workspace = Workspace.objects.get(slug=self.workspace_slug)
        return {"workspace_id": workspace.id}

    def get(self, request, slug, pk):
        instance = self.get_object()
        return Response(
            self.serializer_class(
                instance,
                fields=self.fields,
                expand=self.expand,
                context=self.get_serializer_context(),
            ).data
        )

    def patch(self, request, slug, pk):
        workspace = Workspace.objects.get(slug=slug)
        instance = self.get_object()
        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=True,
            context={"workspace_id": workspace.id},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save()
            _record_agent_config_outbox(workspace, self.entity_type, "update", instance, self.serializer_class)
        return Response(self.serializer_class(instance, context={"workspace_id": workspace.id}).data)

    def delete(self, request, slug, pk):
        workspace = Workspace.objects.get(slug=slug)
        instance = self.get_object()
        with transaction.atomic():
            payload = _json_payload(self.serializer_class(instance, context={"workspace_id": workspace.id}).data)
            instance.delete()
            AgentConfigOutbox.objects.create(
                workspace=workspace,
                entity_type=self.entity_type,
                entity_id=instance.id,
                operation="delete",
                payload=payload,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentUserAgentListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentUserAgent
    serializer_class = AgentUserAgentSerializer
    entity_type = "agent_user_agent"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "prompt_bindings__prompt",
                "prompt_bindings__prompt_version",
                "prompt_bindings__pinned_version",
                "prompt_bindings__role",
            )
        )


class AgentUserAgentDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentUserAgent
    serializer_class = AgentUserAgentSerializer
    entity_type = "agent_user_agent"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "prompt_bindings__prompt",
                "prompt_bindings__prompt_version",
                "prompt_bindings__pinned_version",
                "prompt_bindings__role",
            )
        )


class AgentPromptListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentPrompt
    serializer_class = AgentPromptSerializer
    entity_type = "agent_prompt"


class AgentPromptDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentPrompt
    serializer_class = AgentPromptSerializer
    entity_type = "agent_prompt"


class AgentPromptVersionListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentPromptVersion
    serializer_class = AgentPromptVersionSerializer
    entity_type = "agent_prompt_version"


class AgentPromptVersionDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentPromptVersion
    serializer_class = AgentPromptVersionSerializer
    entity_type = "agent_prompt_version"


class AgentRoleListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentRole
    serializer_class = AgentRoleSerializer
    entity_type = "agent_role"


class AgentRoleDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentRole
    serializer_class = AgentRoleSerializer
    entity_type = "agent_role"


class AgentPromptBindingListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentPromptBinding
    serializer_class = AgentPromptBindingSerializer
    entity_type = "agent_prompt_binding"


class AgentPromptBindingDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentPromptBinding
    serializer_class = AgentPromptBindingSerializer
    entity_type = "agent_prompt_binding"


class AgentWorkerCardListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentWorkerCard
    serializer_class = AgentWorkerCardSerializer
    entity_type = "agent_worker_card"


class AgentWorkerCardDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentWorkerCard
    serializer_class = AgentWorkerCardSerializer
    entity_type = "agent_worker_card"


class AgentUserSecretKeyListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentUserSecretKey
    serializer_class = AgentUserSecretKeySerializer
    entity_type = "agent_user_secret_key"


class AgentUserSecretKeyDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentUserSecretKey
    serializer_class = AgentUserSecretKeySerializer
    entity_type = "agent_user_secret_key"


class AgentProjectWorkspaceListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentProjectWorkspace
    serializer_class = AgentProjectWorkspaceSerializer
    entity_type = "agent_project_workspace"


class AgentProjectWorkspaceDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentProjectWorkspace
    serializer_class = AgentProjectWorkspaceSerializer
    entity_type = "agent_project_workspace"


class AgentRepositoryListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentRepository
    serializer_class = AgentRepositorySerializer
    entity_type = "agent_repository"


class AgentRepositoryDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentRepository
    serializer_class = AgentRepositorySerializer
    entity_type = "agent_repository"


class AgentWorkDirectoryListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentWorkDirectory
    serializer_class = AgentWorkDirectorySerializer
    entity_type = "agent_work_directory"

    def get_queryset(self):
        return super().get_queryset().select_related("default_worker_card")


class AgentWorkDirectoryDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentWorkDirectory
    serializer_class = AgentWorkDirectorySerializer
    entity_type = "agent_work_directory"

    def get_queryset(self):
        return super().get_queryset().select_related("default_worker_card")


class AgentWorkDirectoryRepositoryListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentWorkDirectoryRepository
    serializer_class = AgentWorkDirectoryRepositorySerializer
    entity_type = "agent_work_directory_repository"

    def get_queryset(self):
        return super().get_queryset().select_related("work_directory", "repository")


class AgentWorkDirectoryRepositoryDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentWorkDirectoryRepository
    serializer_class = AgentWorkDirectoryRepositorySerializer
    entity_type = "agent_work_directory_repository"

    def get_queryset(self):
        return super().get_queryset().select_related("work_directory", "repository")


class AgentWorkerMountListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentWorkerMount
    serializer_class = AgentWorkerMountSerializer
    entity_type = "agent_worker_mount"

    def get_queryset(self):
        return super().get_queryset().select_related("work_directory", "worker_card")


class AgentWorkerMountDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentWorkerMount
    serializer_class = AgentWorkerMountSerializer
    entity_type = "agent_worker_mount"

    def get_queryset(self):
        return super().get_queryset().select_related("work_directory", "worker_card")


class AgentProjectDefaultListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentProjectDefault
    serializer_class = AgentProjectDefaultSerializer
    entity_type = "agent_project_default"

    def get_queryset(self):
        return super().get_queryset().select_related("project", "work_directory", "worker_card")


class AgentProjectDefaultDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentProjectDefault
    serializer_class = AgentProjectDefaultSerializer
    entity_type = "agent_project_default"

    def get_queryset(self):
        return super().get_queryset().select_related("project", "work_directory", "worker_card")


class AgentTaskWorkDirectoryOverrideListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentTaskWorkDirectoryOverride
    serializer_class = AgentTaskWorkDirectoryOverrideSerializer
    entity_type = "agent_task_work_directory_override"

    def get_queryset(self):
        return super().get_queryset().select_related("issue", "work_directory", "worker_card")


class AgentTaskWorkDirectoryOverrideDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentTaskWorkDirectoryOverride
    serializer_class = AgentTaskWorkDirectoryOverrideSerializer
    entity_type = "agent_task_work_directory_override"

    def get_queryset(self):
        return super().get_queryset().select_related("issue", "work_directory", "worker_card")


class AgentTaskContextDocumentListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentTaskContextDocument
    serializer_class = AgentTaskContextDocumentSerializer
    entity_type = "agent_task_context_document"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("issue", "issue__project").prefetch_related("versions")
        issue_id = self.request.GET.get("issue_id")
        document_type = self.request.GET.get("document_type")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return queryset

    def post(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        serializer = self.serializer_class(data=request.data, context={"workspace_id": workspace.id})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save(workspace=workspace)
            _record_task_context_document_version(instance, "Created task context document.", request)
            _record_task_context_progress(
                instance.issue,
                f"Created {instance.document_type}.md.",
                request,
                entry_type="progress",
                source="system",
            )
            _record_agent_config_outbox(workspace, self.entity_type, "create", instance, self.serializer_class)
        return Response(
            self.serializer_class(instance, context={"workspace_id": workspace.id}).data,
            status=status.HTTP_201_CREATED,
        )


class AgentTaskContextDocumentDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentTaskContextDocument
    serializer_class = AgentTaskContextDocumentSerializer
    entity_type = "agent_task_context_document"

    def get_queryset(self):
        return super().get_queryset().select_related("issue", "issue__project").prefetch_related("versions")

    def patch(self, request, slug, pk):
        workspace = Workspace.objects.get(slug=slug)
        instance = self.get_object()
        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=True,
            context={"workspace_id": workspace.id},
        )
        serializer.is_valid(raise_exception=True)
        should_version = any(field in request.data for field in ["body", "body_format", "title"])
        with transaction.atomic():
            if should_version:
                serializer.validated_data["version"] = instance.version + 1
            instance = serializer.save()
            if should_version:
                _record_task_context_document_version(instance, "Updated task context document.", request)
                _record_task_context_progress(
                    instance.issue,
                    f"Updated {instance.document_type}.md to version {instance.version}.",
                    request,
                    entry_type="progress",
                    source="system",
                )
            _record_agent_config_outbox(workspace, self.entity_type, "update", instance, self.serializer_class)
        return Response(self.serializer_class(instance, context={"workspace_id": workspace.id}).data)


class AgentTaskContextDocumentVersionListAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        queryset = AgentTaskContextDocumentVersion.objects.filter(workspace__slug=slug).select_related(
            "document",
            "issue",
        )
        document_id = request.GET.get("document_id")
        issue_id = request.GET.get("issue_id")
        document_type = request.GET.get("document_type")
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        queryset = queryset.order_by(request.GET.get("order_by", "-version"))
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda results: AgentTaskContextDocumentVersionSerializer(results, many=True).data,
        )


class AgentTaskProgressEntryListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentTaskProgressEntry
    serializer_class = AgentTaskProgressEntrySerializer
    entity_type = "agent_task_progress_entry"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("issue", "issue__project", "author")
        issue_id = self.request.GET.get("issue_id")
        source = self.request.GET.get("source")
        entry_type = self.request.GET.get("entry_type")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if source:
            queryset = queryset.filter(source=source)
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        return queryset


class AgentTaskWorkflowInstanceListCreateAPIEndpoint(AgentConfigSourceListCreateAPIEndpoint):
    model = AgentTaskWorkflowInstance
    serializer_class = AgentTaskWorkflowInstanceSerializer
    entity_type = "agent_task_workflow_instance"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("issue", "issue__project", "active_node", "default_agent")
            .prefetch_related("nodes__assigned_agent")
        )
        issue_id = self.request.GET.get("issue_id")
        project_id = self.request.GET.get("project_id")
        status_value = self.request.GET.get("status")
        active_node_key = self.request.GET.get("active_node_key")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if project_id:
            queryset = queryset.filter(issue__project_id=project_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if active_node_key:
            queryset = queryset.filter(active_node__key=active_node_key)
        return queryset

    def post(self, request, slug):
        issue_id = request.data.get("issue")
        if not issue_id:
            return Response({"issue": "Issue is required."}, status=status.HTTP_400_BAD_REQUEST)
        issue = get_object_or_404(Issue, id=issue_id, workspace__slug=slug)
        workflow = ensure_default_task_workflow_instance(issue, actor=request.user)
        if request.data.get("default_agent"):
            default_agent = get_object_or_404(
                AgentUserAgent,
                id=request.data["default_agent"],
                workspace__slug=slug,
            )
            workflow.default_agent = default_agent
            workflow.save(update_fields=["default_agent", "updated_at"])
            _record_agent_config_outbox(
                workflow.workspace,
                self.entity_type,
                "update",
                workflow,
                self.serializer_class,
            )
        return Response(
            self.serializer_class(workflow, context={"workspace_id": workflow.workspace_id}).data,
            status=status.HTTP_201_CREATED,
        )


class AgentTaskWorkflowInstanceDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentTaskWorkflowInstance
    serializer_class = AgentTaskWorkflowInstanceSerializer
    entity_type = "agent_task_workflow_instance"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("issue", "issue__project", "active_node", "default_agent")
            .prefetch_related("nodes__assigned_agent")
        )


class AgentTaskWorkflowNodeListAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        queryset = AgentTaskWorkflowNode.objects.filter(workspace__slug=slug).select_related(
            "workflow_instance",
            "issue",
            "assigned_agent",
        )
        issue_id = request.GET.get("issue_id")
        workflow_instance_id = request.GET.get("workflow_instance_id")
        node_type = request.GET.get("node_type")
        status_value = request.GET.get("status")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if workflow_instance_id:
            queryset = queryset.filter(workflow_instance_id=workflow_instance_id)
        if node_type:
            queryset = queryset.filter(node_type=node_type)
        if status_value:
            queryset = queryset.filter(status=status_value)
        queryset = queryset.order_by(request.GET.get("order_by", "sort_order"))
        workspace = Workspace.objects.get(slug=slug)
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda results: AgentTaskWorkflowNodeSerializer(
                results,
                many=True,
                context={"workspace_id": workspace.id},
            ).data,
        )


class AgentTaskWorkflowNodeDetailAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    def get_object(self, slug, pk):
        return get_object_or_404(
            AgentTaskWorkflowNode.objects.select_related("workflow_instance", "issue", "assigned_agent"),
            id=pk,
            workspace__slug=slug,
        )

    def get(self, request, slug, pk):
        node = self.get_object(slug, pk)
        return Response(AgentTaskWorkflowNodeSerializer(node, context={"workspace_id": node.workspace_id}).data)

    def patch(self, request, slug, pk):
        node = self.get_object(slug, pk)
        serializer = AgentTaskWorkflowNodeSerializer(
            node,
            data=request.data,
            partial=True,
            context={"workspace_id": node.workspace_id},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            node = serializer.save()
            _record_agent_config_outbox(
                node.workspace,
                "agent_task_workflow_node",
                "update",
                node,
                AgentTaskWorkflowNodeSerializer,
            )
        return Response(AgentTaskWorkflowNodeSerializer(node, context={"workspace_id": node.workspace_id}).data)


class AgentTaskWorkflowTransitionListAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        queryset = AgentTaskWorkflowTransition.objects.filter(workspace__slug=slug).select_related(
            "workflow_instance",
            "issue",
            "from_node",
            "to_node",
            "actor",
        )
        issue_id = request.GET.get("issue_id")
        workflow_instance_id = request.GET.get("workflow_instance_id")
        action = request.GET.get("action")
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        if workflow_instance_id:
            queryset = queryset.filter(workflow_instance_id=workflow_instance_id)
        if action:
            queryset = queryset.filter(action=action)
        queryset = queryset.order_by(request.GET.get("order_by", "created_at"))
        workspace = Workspace.objects.get(slug=slug)
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda results: AgentTaskWorkflowTransitionSerializer(
                results,
                many=True,
                context={"workspace_id": workspace.id},
            ).data,
        )


class AgentTaskWorkflowActionAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    def post(self, request, slug):
        serializer = AgentTaskWorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            workflow = _resolve_task_workflow_for_action(slug, data)
            result = _apply_task_workflow_action(workflow, data, request)
        return Response(result, status=status.HTTP_200_OK)


class AgentTaskContextSnapshotAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        project_id = request.GET.get("project_id")
        work_item_id = request.GET.get("work_item_id")
        worker_id = request.GET.get("worker_id")
        if not project_id or not work_item_id:
            return Response(
                {"error": "project_id and work_item_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_object_or_404(Project, id=project_id, workspace__slug=slug)
        issue = _resolve_agent_run_issue(slug, project.id, str(work_item_id))
        work_directory_context = _resolve_work_directory_context(slug, project, issue, worker_id)
        return Response(_build_task_context_snapshot_payload(slug, project, issue, work_directory_context))


class AgentWorkDirectoryResolutionAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        project_id = request.GET.get("project_id")
        work_item_id = request.GET.get("work_item_id")
        worker_id = request.GET.get("worker_id")
        if not project_id:
            return Response({"error": "project_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        project = get_object_or_404(Project, id=project_id, workspace__slug=slug)
        issue = _resolve_agent_run_issue(slug, project.id, str(work_item_id)) if work_item_id else None
        selected = _resolve_work_directory_context(slug, project, issue, worker_id)
        return Response(_build_work_directory_context_payload(selected))


class AgentRunIntentAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    def post(self, request, slug):
        acp_base_url = os.environ.get("AGENT_CONTROL_PLANE_URL", "").strip().rstrip("/")
        if not acp_base_url:
            return Response(
                {"error": "AGENT_CONTROL_PLANE_URL is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        project_id = request.data.get("project_id")
        work_item_id = request.data.get("work_item_id")
        repository_id = request.data.get("repository_id")
        work_directory_id = request.data.get("work_directory_id")
        agent_id = request.data.get("agent_id")
        worker_id = request.data.get("worker_id")
        if not project_id or not work_item_id:
            return Response(
                {"error": "project_id and work_item_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_object_or_404(Project, id=project_id, workspace__slug=slug)
        issue = _resolve_agent_run_issue(slug, project.id, str(work_item_id))
        agent = None
        if agent_id:
            agent = get_object_or_404(
                AgentUserAgent,
                id=agent_id,
                workspace__slug=slug,
            )
        repository = None
        if repository_id:
            repository = get_object_or_404(
                AgentRepository,
                id=repository_id,
                workspace__slug=slug,
                project=project,
            )
        work_directory = None
        if work_directory_id:
            work_directory = get_object_or_404(
                AgentWorkDirectory,
                id=work_directory_id,
                workspace__slug=slug,
            )
        worker = None
        if worker_id:
            worker = get_object_or_404(
                AgentWorkerCard,
                id=worker_id,
                workspace__slug=slug,
            )

        selected = _resolve_work_directory_context(slug, project, issue, worker_id, work_directory=work_directory)
        worker = worker or selected["worker"]
        payload = _build_agent_run_intent_payload(request, slug, project, issue, agent, repository, worker, selected)
        headers = {"Content-Type": "application/json"}
        token = os.environ.get("AGENT_CONTROL_PLANE_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.post(
                f"{acp_base_url}/api/runs",
                json=payload,
                headers=headers,
                timeout=10,
            )
        except requests.RequestException as exc:
            return Response(
                {"error": "Agent Control Plane is unavailable.", "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            response_payload = response.json()
        except ValueError:
            response_payload = {"error": response.text}

        if response.status_code >= 400:
            return Response(response_payload, status=status.HTTP_502_BAD_GATEWAY)

        return Response(response_payload, status=status.HTTP_201_CREATED)


class AgentConfigOutboxAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    use_read_replica = True

    def get(self, request, slug):
        after_id = int(request.GET.get("after_id", 0))
        limit = min(int(request.GET.get("limit", 100)), 500)
        queryset = AgentConfigOutbox.objects.filter(
            workspace__slug=slug,
            id__gt=after_id,
        ).order_by("id")[:limit]
        return Response(AgentConfigOutboxSerializer(queryset, many=True).data)


def _resolve_agent_run_issue(slug, project_id, work_item_id):
    queryset = Issue.issue_objects.select_related("state", "project").filter(
        workspace__slug=slug,
        project_id=project_id,
    )
    issue = queryset.filter(id=work_item_id).first()
    if issue:
        return issue

    if "-" in work_item_id:
        sequence = work_item_id.rsplit("-", 1)[-1]
        if sequence.isdigit():
            issue = queryset.filter(sequence_id=int(sequence)).first()
            if issue:
                return issue

    if work_item_id.isdigit():
        return get_object_or_404(queryset, sequence_id=int(work_item_id))

    raise Http404


def _build_agent_run_intent_payload(
    request,
    slug,
    project,
    issue,
    agent,
    repository,
    worker,
    work_directory_context=None,
):
    identifier = f"{project.identifier}-{issue.sequence_id}"
    payload = {
        "source": "plane",
        "planeProjectId": str(project.id),
        "projectSlug": project.identifier.lower(),
        "externalTaskId": str(issue.id),
        "identifier": identifier,
        "title": issue.name,
        "state": _agent_run_workflow_state(issue.state),
        "priority": _agent_run_priority(issue.priority),
        "url": request.build_absolute_uri(f"/{slug}/browse/{identifier}/"),
    }

    if agent:
        payload.update(
            {
                "agentId": str(agent.id),
                "agentKey": agent.key,
                "agentName": agent.name,
                "agentRuntime": agent.runtime,
                "agentModel": agent.model,
            }
        )

    if repository:
        payload.update(
            {
                "repositoryId": str(repository.id),
                "repositoryKey": repository.key,
                "repositoryUrl": repository.clone_url or repository.url,
            }
        )

    if work_directory_context and work_directory_context["work_directory"]:
        payload["workDirectory"] = _build_work_directory_context_payload(work_directory_context)

    if worker:
        payload.update(
            {
                "workerCardId": str(worker.id),
                "workerKey": worker.key,
                "workerName": worker.name,
                "workerEndpoint": worker.worker_endpoint,
            }
        )

    prompt_version_ids = _clean_agent_run_string_list(request.data.get("prompt_version_ids"))
    if prompt_version_ids:
        payload["promptVersionIds"] = prompt_version_ids

    available_secret_keys = _clean_agent_run_string_list(request.data.get("available_secret_keys"))
    if available_secret_keys:
        payload["availableSecretKeys"] = available_secret_keys

    return payload


def _resolve_work_directory_context(slug, project, issue=None, worker_id=None, work_directory=None):
    task_override = None
    project_default = None
    if issue is not None:
        task_override = (
            AgentTaskWorkDirectoryOverride.objects.select_related("work_directory", "worker_card")
            .filter(issue=issue, workspace__slug=slug, is_active=True)
            .first()
        )
    project_default = (
        AgentProjectDefault.objects.select_related("work_directory", "worker_card")
        .filter(project=project, workspace__slug=slug, is_active=True)
        .first()
    )

    source = "explicit" if work_directory is not None else "none"
    if work_directory is None and task_override and task_override.work_directory:
        work_directory = task_override.work_directory
        source = "task_override"
    if work_directory is None and project_default and project_default.work_directory:
        work_directory = project_default.work_directory
        source = "project_default"

    worker = None
    if worker_id:
        worker = get_object_or_404(AgentWorkerCard, id=worker_id, workspace__slug=slug)
    if worker is None and task_override and task_override.worker_card:
        worker = task_override.worker_card
    if worker is None and project_default and project_default.worker_card:
        worker = project_default.worker_card
    if worker is None and work_directory and work_directory.default_worker_card_id:
        worker = work_directory.default_worker_card

    mount = None
    if work_directory and worker:
        mount = (
            AgentWorkerMount.objects.filter(
                workspace__slug=slug,
                work_directory=work_directory,
                worker_card=worker,
                is_active=True,
            )
            .select_related("work_directory", "worker_card")
            .first()
        )

    repositories = []
    if work_directory:
        repositories = list(
            AgentWorkDirectoryRepository.objects.filter(
                workspace__slug=slug,
                work_directory=work_directory,
                is_active=True,
            )
            .select_related("repository")
            .order_by("sort_order", "repository__name")
        )

    return {
        "source": source,
        "project": project,
        "issue": issue,
        "task_override": task_override,
        "project_default": project_default,
        "work_directory": work_directory,
        "worker": worker,
        "mount": mount,
        "repositories": repositories,
    }


def _build_work_directory_context_payload(selected):
    work_directory = selected["work_directory"]
    worker = selected["worker"]
    mount = selected["mount"]
    payload = {
        "source": selected["source"],
        "projectId": str(selected["project"].id),
        "workItemId": str(selected["issue"].id) if selected["issue"] else None,
        "workDirectory": None,
        "worker": None,
        "mount": None,
        "repositories": [],
    }
    if work_directory:
        payload["workDirectory"] = {
            "id": str(work_directory.id),
            "key": work_directory.key,
            "name": work_directory.name,
            "rootPath": work_directory.root_path,
            "worktreeStrategy": work_directory.worktree_strategy,
            "branchPolicy": work_directory.branch_policy,
            "prdPath": work_directory.prd_path,
            "statusPath": work_directory.status_path,
            "progressPath": work_directory.progress_path,
        }
    if worker:
        payload["worker"] = {
            "id": str(worker.id),
            "key": worker.key,
            "name": worker.name,
            "endpoint": worker.worker_endpoint,
        }
    if mount:
        payload["mount"] = {
            "id": str(mount.id),
            "localPath": mount.local_path,
            "isDefault": mount.is_default,
        }
    for link in selected["repositories"]:
        repository = link.repository
        payload["repositories"].append(
            {
                "id": str(repository.id),
                "key": repository.key,
                "provider": repository.scm_provider or repository.provider,
                "name": repository.name,
                "fullName": repository.full_name,
                "url": repository.clone_url or repository.url,
                "relativePath": link.relative_path,
                "defaultBranch": link.default_branch,
                "worktreeStrategy": link.worktree_strategy,
                "isRequired": link.is_required,
            }
        )
    return payload


def _record_task_context_document_version(document, change_summary, request):
    return AgentTaskContextDocumentVersion.objects.create(
        workspace=document.workspace,
        document=document,
        issue=document.issue,
        document_type=document.document_type,
        version=document.version,
        body=document.body,
        body_format=document.body_format,
        change_summary=change_summary,
        source=_agent_task_context_request_source(request),
    )


def _record_task_context_progress(issue, body, request, entry_type="progress", source=None):
    user = getattr(request, "user", None)
    author = user if getattr(user, "is_authenticated", False) else None
    progress = AgentTaskProgressEntry.objects.create(
        workspace=issue.workspace,
        issue=issue,
        entry_type=entry_type,
        source=source or _agent_task_context_request_source(request),
        body=body,
        author=author,
    )
    AgentConfigOutbox.objects.create(
        workspace=issue.workspace,
        entity_type="agent_task_progress_entry",
        entity_id=progress.id,
        operation="create",
        payload=_json_payload(
            AgentTaskProgressEntrySerializer(progress, context={"workspace_id": issue.workspace_id}).data
        ),
    )
    return progress


def _resolve_task_workflow_for_action(slug, data):
    workflow = None
    if data.get("workflow_instance"):
        workflow = AgentTaskWorkflowInstance.objects.select_for_update().filter(
            id=data["workflow_instance"],
            workspace__slug=slug,
            is_active=True,
        ).first()
    elif data.get("issue"):
        issue = get_object_or_404(Issue, id=data["issue"], workspace__slug=slug)
        workflow = ensure_default_task_workflow_instance(issue)
        workflow = AgentTaskWorkflowInstance.objects.select_for_update().get(id=workflow.id)
    if workflow is None:
        raise Http404
    return workflow


def _apply_task_workflow_action(workflow, data, request):
    workspace = workflow.workspace
    nodes = {
        node.key: node
        for node in AgentTaskWorkflowNode.objects.select_for_update()
        .filter(workflow_instance=workflow, is_active=True)
    }
    from_node = _resolve_task_workflow_action_node(workflow, nodes, data)
    action = data["action"]

    if action in {"set_auto", "set_manual"}:
        mode = "auto" if action == "set_auto" else "manual"
        from_node.mode = mode
        from_node.save(update_fields=["mode", "updated_at"])
        transition = _create_task_workflow_transition(workflow, from_node, from_node, action, request, data)
        _record_agent_config_outbox(
            workspace,
            "agent_task_workflow_node",
            "update",
            from_node,
            AgentTaskWorkflowNodeSerializer,
        )
        _record_agent_config_outbox(
            workspace,
            "agent_task_workflow_transition",
            "create",
            transition,
            AgentTaskWorkflowTransitionSerializer,
        )
        _record_task_context_progress(
            workflow.issue,
            f"Set workflow node {from_node.name} to {mode} mode.",
            request,
            entry_type="decision",
            source="system",
        )
        return _serialize_task_workflow_action_result(workflow, transition)

    target_node = _resolve_task_workflow_target_node(nodes, from_node, action, data)
    now = timezone.now()
    if action == "agent_failed":
        from_node.status = "failed"
        from_node.completed_at = now
        workflow.status = "blocked"
    elif action == "block":
        from_node.status = "blocked"
        workflow.status = "blocked"
    else:
        from_node.status = "completed"
        from_node.completed_at = now
        workflow.status = "done" if target_node.key == "done" else "active"

    target_node.status = "active"
    if target_node.started_at is None:
        target_node.started_at = now
    workflow.active_node = target_node

    from_node.save(update_fields=["status", "completed_at", "updated_at"])
    target_node.save(update_fields=["status", "started_at", "updated_at"])
    workflow.save(update_fields=["status", "active_node", "updated_at"])
    _sync_task_workflow_issue_state(workflow.issue, target_node)
    transition = _create_task_workflow_transition(workflow, from_node, target_node, action, request, data)
    for instance, entity_type, serializer_class in [
        (from_node, "agent_task_workflow_node", AgentTaskWorkflowNodeSerializer),
        (target_node, "agent_task_workflow_node", AgentTaskWorkflowNodeSerializer),
        (workflow, "agent_task_workflow_instance", AgentTaskWorkflowInstanceSerializer),
        (transition, "agent_task_workflow_transition", AgentTaskWorkflowTransitionSerializer),
    ]:
        operation = "create" if instance is transition else "update"
        _record_agent_config_outbox(workspace, entity_type, operation, instance, serializer_class)
    _record_task_context_progress(
        workflow.issue,
        _task_workflow_progress_body(action, from_node, target_node),
        request,
        entry_type="decision" if action in {"approve", "return", "block"} else "feedback",
        source="system",
    )
    return _serialize_task_workflow_action_result(workflow, transition)


def _resolve_task_workflow_action_node(workflow, nodes, data):
    if data.get("node"):
        for node in nodes.values():
            if str(node.id) == str(data["node"]):
                return node
        raise Http404
    if data.get("node_key"):
        node = nodes.get(data["node_key"])
        if node is None:
            raise Http404
        return node
    if workflow.active_node_id:
        for node in nodes.values():
            if node.id == workflow.active_node_id:
                return node
    raise Http404


def _resolve_task_workflow_target_node(nodes, from_node, action, data):
    if action in {"agent_failed", "block"}:
        target_key = "blocked"
    elif action == "return":
        target_key = data.get("target_node_key") or "development"
    else:
        target_key = data.get("target_node_key") or _default_task_workflow_exit(from_node)
    target_node = nodes.get(target_key)
    if target_node is None:
        raise Http404
    if target_key == from_node.key and action != "approve":
        return target_node
    allowed_exits = set(from_node.main_exits or [])
    if action == "return":
        allowed_exits.update(["intake", "development", "human_review", "merged_gate", "released_gate", "deployed_gate"])
    if target_key not in allowed_exits and target_key != "blocked":
        raise Http404
    return target_node


def _default_task_workflow_exit(node):
    exits = [exit_key for exit_key in (node.main_exits or []) if exit_key != "blocked"]
    if not exits:
        raise Http404
    return exits[0]


def _create_task_workflow_transition(workflow, from_node, to_node, action, request, data):
    actor = request.user if getattr(request.user, "is_authenticated", False) else None
    transition = AgentTaskWorkflowTransition.objects.create(
        workspace=workflow.workspace,
        workflow_instance=workflow,
        issue=workflow.issue,
        from_node=from_node,
        to_node=to_node,
        action=action,
        reason=data.get("reason", ""),
        actor=actor,
        metadata=data.get("metadata") or {},
    )
    return transition


def _sync_task_workflow_issue_state(issue, node):
    from plane.db.models.agent import _sync_issue_state_to_workflow_node

    _sync_issue_state_to_workflow_node(issue, node)


def _task_workflow_progress_body(action, from_node, target_node):
    return {
        "approve": f"Approved {from_node.name}; moved workflow to {target_node.name}.",
        "return": f"Returned workflow from {from_node.name} to {target_node.name}.",
        "block": f"Blocked workflow at {from_node.name}; moved to {target_node.name}.",
        "agent_failed": f"Agent node {from_node.name} failed; moved workflow to {target_node.name}.",
    }.get(action, f"Moved workflow from {from_node.name} to {target_node.name}.")


def _serialize_task_workflow_action_result(workflow, transition):
    workflow = (
        AgentTaskWorkflowInstance.objects.select_related("issue", "issue__project", "active_node", "default_agent")
        .prefetch_related("nodes__assigned_agent")
        .get(id=workflow.id)
    )
    context = {"workspace_id": workflow.workspace_id}
    return {
        "workflow": AgentTaskWorkflowInstanceSerializer(workflow, context=context).data,
        "transition": AgentTaskWorkflowTransitionSerializer(transition, context=context).data,
    }


def _agent_task_context_request_source(request):
    return request.data.get("source") if getattr(request, "data", None) and request.data.get("source") else "human"


def _build_task_context_snapshot_payload(slug, project, issue, work_directory_context):
    documents = {
        document.document_type: document
        for document in AgentTaskContextDocument.objects.filter(
            workspace__slug=slug,
            issue=issue,
            is_active=True,
        ).prefetch_related("versions")
    }
    progress_entries = list(
        AgentTaskProgressEntry.objects.filter(
            workspace__slug=slug,
            issue=issue,
            is_active=True,
        )
        .select_related("author")
        .order_by("occurred_at", "created_at")
    )
    human_comments = list(issue.issue_comments.filter(access="INTERNAL").select_related("actor").order_by("created_at"))
    context = {"workspace_id": issue.workspace_id}
    rendered_progress = "\n\n".join(
        f"## {entry.occurred_at.isoformat()} [{entry.source}/{entry.entry_type}]\n\n{entry.body}"
        for entry in progress_entries
    )
    return {
        "source": "plane",
        "workspaceSlug": slug,
        "project": {
            "id": str(project.id),
            "identifier": project.identifier,
            "name": project.name,
        },
        "task": {
            "id": str(issue.id),
            "identifier": f"{project.identifier}-{issue.sequence_id}",
            "title": issue.name,
            "state": _agent_run_workflow_state(issue.state),
        },
        "documents": {
            "prd": AgentTaskContextDocumentSerializer(documents["prd"], context=context).data
            if "prd" in documents
            else None,
            "status": AgentTaskContextDocumentSerializer(documents["status"], context=context).data
            if "status" in documents
            else None,
        },
        "progressEntries": AgentTaskProgressEntrySerializer(progress_entries, many=True, context=context).data,
        "renderedProgress": rendered_progress,
        "humanComments": [
            {
                "id": str(comment.id),
                "body": comment.comment_stripped,
                "html": comment.comment_html,
                "actor": str(comment.actor_id) if comment.actor_id else None,
                "createdAt": comment.created_at.isoformat(),
            }
            for comment in human_comments
        ],
        "workDirectory": _build_work_directory_context_payload(work_directory_context),
    }


def _clean_agent_run_string_list(value):
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _agent_run_priority(priority):
    return {
        "urgent": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
        "none": 5,
    }.get(priority)


def _agent_run_workflow_state(state):
    if not state:
        return "Todo"

    normalized_name = (state.name or "").strip()
    if normalized_name in {
        "Backlog",
        "Todo",
        "Development",
        "Code Review",
        "Human Review",
        "In Merge",
        "Merged",
        "Release Version",
        "Released",
        "Deployment",
        "Deployed",
        "Blocked",
        "Done",
        "Canceled",
        "Duplicate",
    }:
        return normalized_name

    return {
        "backlog": "Backlog",
        "unstarted": "Todo",
        "started": "Development",
        "completed": "Done",
        "cancelled": "Canceled",
        "canceled": "Canceled",
        "triage": "Backlog",
    }.get((state.group or "").strip().lower(), "Todo")
