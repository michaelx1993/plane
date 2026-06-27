/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { ListChecks } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function TasksCenterPage() {
  return (
    <AgentControlCenterPage
      title="Tasks Center"
      subtitle="Agent tasks, human gates, blocked nodes, and recent execution progress."
      Icon={ListChecks}
      metrics={[
        { label: "Running Agents", value: "0" },
        { label: "Waiting Human Gates", value: "0" },
        { label: "Failed / Blocked Nodes", value: "0" },
        { label: "Active Tasks", value: "0" },
      ]}
      lists={[
        {
          title: "Attention Queue",
          items: ["Human gates waiting for review", "Failed agent nodes", "Blocked tasks"],
        },
        {
          title: "Recent Progress",
          items: ["Agent conclusions", "Human decisions", "Release and deployment evidence"],
        },
      ]}
    />
  );
}
