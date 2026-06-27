/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { WorkerDirectoryPage } from "@/components/agent-control-center/worker-directory-page";

export default function WorkDirectoriesPage({ params }: { params: { workspaceSlug: string } }) {
  return <WorkerDirectoryPage initialView="work-directories" workspaceSlug={params.workspaceSlug} />;
}
