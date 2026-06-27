/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { FolderGit2 } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function WorkDirectoriesPage() {
  return (
    <AgentControlCenterPage
      title="Work Directories"
      subtitle="Project work directories, repositories, worker mount paths, branch policy, and worktree strategy."
      Icon={FolderGit2}
      lists={[
        {
          title: "Directory Registry",
          items: ["Root Path", "Repositories", "Worker Mounts", "Worktree Strategy", "Recent Tasks"],
        },
      ]}
    />
  );
}
