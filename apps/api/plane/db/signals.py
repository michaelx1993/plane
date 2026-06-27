# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db.models.signals import post_save
from django.dispatch import receiver

from plane.db.models.agent import ensure_default_task_workflow_instance
from plane.db.models.issue import Issue


@receiver(post_save, sender=Issue)
def create_default_agent_task_workflow(sender, instance, created, **kwargs):
    if not created:
        return
    ensure_default_task_workflow_instance(instance)
