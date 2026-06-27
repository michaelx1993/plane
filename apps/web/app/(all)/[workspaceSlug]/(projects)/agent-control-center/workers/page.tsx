/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { HardDrive } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function WorkersPage() {
  return (
    <AgentControlCenterPage
      title="Workers"
      subtitle="Execution hosts, capabilities, heartbeat, work directory access, and recent runs."
      Icon={HardDrive}
      lists={[
        {
          title: "Worker Cards",
          items: ["Mac Studio Worker", "MBP Worker", "Remote Linux Worker"],
        },
      ]}
    />
  );
}
