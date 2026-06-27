/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Workflow } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function WorkflowsPage() {
  return (
    <AgentControlCenterPage
      title="Workflows"
      subtitle="Default software delivery workflow, active nodes, human gates, and task-specific overrides."
      Icon={Workflow}
      lists={[
        {
          title: "Default Workflow",
          items: ["To-do / Intake / PRD", "Development", "Code Review", "Human Gates", "Release", "Deployment"],
        },
      ]}
    />
  );
}
