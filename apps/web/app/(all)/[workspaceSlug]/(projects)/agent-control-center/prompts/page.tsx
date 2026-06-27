/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { FileText } from "lucide-react";

import { AgentControlCenterPage } from "@/components/agent-control-center/center-page";

export default function PromptsPage() {
  return (
    <AgentControlCenterPage
      title="Prompts"
      subtitle="Prompt library, versions, bindings, scopes, kinds, and preview."
      Icon={FileText}
      lists={[
        {
          title: "Prompt Library",
          items: ["Prompt Metadata", "Latest Version", "Version History", "Bindings", "Preview"],
        },
      ]}
    />
  );
}
