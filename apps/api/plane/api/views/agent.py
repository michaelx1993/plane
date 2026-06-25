# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import WorkspaceEntityPermission
from plane.api.serializers import (
    AgentConfigOutboxSerializer,
    AgentPromptBindingSerializer,
    AgentPromptSerializer,
    AgentPromptVersionSerializer,
    AgentProjectWorkspaceSerializer,
    AgentRepositorySerializer,
    AgentRoleSerializer,
    AgentUserAgentSerializer,
    AgentWorkerCardSerializer,
)
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
    Workspace,
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


class AgentUserAgentDetailAPIEndpoint(AgentConfigSourceDetailAPIEndpoint):
    model = AgentUserAgent
    serializer_class = AgentUserAgentSerializer
    entity_type = "agent_user_agent"


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


class AgentConfigOutboxAPIEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]
    use_read_replica = True

    def get(self, request, slug):
        after_id = int(request.GET.get("after_id", 0))
        limit = min(int(request.GET.get("limit", 100)), 500)
        queryset = AgentConfigOutbox.objects.filter(
            workspace__slug=slug,
            id__gt=after_id,
        ).order_by("id")[:limit]
        return Response(AgentConfigOutboxSerializer(queryset, many=True).data)
