/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { AgentPromptLibraryPage } from "@/components/agent-control-center/agent-prompt-library-page";

export default function PromptsPage({ params }: { params: { workspaceSlug: string } }) {
  return <AgentPromptLibraryPage initialView="prompts" workspaceSlug={params.workspaceSlug} />;
}
