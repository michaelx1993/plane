/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Bot } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function AgentsPage() {
  return (
    <AgentControlCenterPage
      title="Agents"
      subtitle="Reusable user-owned agents, prompt stacks, default workers, and workflow node bindings."
      Icon={Bot}
      lists={[
        {
          title: "Agent Library",
          items: ["My Agents", "Prompt Stack", "Default Role", "Default Worker", "Recent Runs"],
        },
      ]}
    />
  );
}
