/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

type ListResponse<T> = T[] | { results?: T[] };
type AgentPlatformError = {
  response?: {
    data?: unknown;
    status?: number;
  };
};

export type AgentPromptScope = "agent" | "project" | "role" | "playbook" | "task" | "workspace";
export type AgentPromptKind =
  | "instruction"
  | "context"
  | "constraint"
  | "workflow"
  | "style"
  | "safety"
  | "output_contract";
export type AgentPromptType = AgentPromptScope | "playbook_task" | "business_system";
export type AgentPromptVersionPolicy = "latest" | "pinned";

export type AgentUserAgent = {
  id: string;
  key: string;
  name: string;
  description: string;
  runtime: string;
  model: string;
  tools: string[];
  defaults: Record<string, unknown>;
  is_default: boolean;
  is_active: boolean;
};

export type AgentPrompt = {
  id: string;
  key: string;
  name: string;
  description: string;
  prompt_type: AgentPromptType;
  scope: AgentPromptScope;
  kind: AgentPromptKind;
  visibility: string;
  status: string;
  latest_version: number;
  is_active: boolean;
};

export type AgentPromptVersion = {
  id: string;
  prompt: string;
  version: number;
  body: string;
  variables: string[];
  content_hash: string;
  changelog: string;
  is_active: boolean;
};

export type AgentRole = {
  id: string;
  key: string;
  name: string;
  description: string;
  prompt: string | null;
  is_active: boolean;
};

export type AgentPromptBinding = {
  id: string;
  agent: string;
  prompt: string;
  prompt_version: string | null;
  target_type: string;
  target_id: string;
  version_policy: AgentPromptVersionPolicy;
  pinned_version: string | null;
  role: string | null;
  slot: string;
  sort_order: number;
  is_required: boolean;
  is_active: boolean;
};

export type AgentWorkerCard = {
  id: string;
  key: string;
  name: string;
  description: string;
  worker_endpoint: string;
  capabilities: string[];
  labels: Record<string, unknown>;
  is_active: boolean;
};

export type AgentProjectWorkspace = {
  id: string;
  project: string;
  worker_card: string | null;
  slug: string;
  name: string;
  local_path: string;
  path_policy: string;
  meta_git_mode: string;
  meta_git_remote_url: string;
  status_path: string;
  progress_path: string;
  meta_path: string;
  is_active: boolean;
};

export type AgentRepository = {
  id: string;
  project: string | null;
  key: string;
  provider: string;
  scm_provider: string;
  owner: string;
  name: string;
  full_name: string;
  url: string;
  clone_url: string;
  default_branch: string;
  credential_key: string;
  worktree_strategy: string;
  local_path: string;
  is_required: boolean;
  is_active: boolean;
};

export type AgentUserSecretKey = {
  id: string;
  owner: string | null;
  key: string;
  description: string;
  provider: string;
  provider_ref: string;
  status: string;
};

export type AgentPlatformWorkspaceSnapshot = {
  agents: AgentUserAgent[];
  prompts: AgentPrompt[];
  promptVersions: AgentPromptVersion[];
  roles: AgentRole[];
  promptBindings: AgentPromptBinding[];
  secretKeys: AgentUserSecretKey[];
};

export type AgentPlatformProjectSnapshot = {
  workerCards: AgentWorkerCard[];
  projectWorkspaces: AgentProjectWorkspace[];
  repositories: AgentRepository[];
};

export type AgentRunIntentPayload = {
  project_id: string;
  work_item_id: string;
  agent_id?: string | null;
  repository_id?: string | null;
  worker_id?: string | null;
  prompt_version_ids?: string[];
  available_secret_keys?: string[];
};

export type AgentRunIntentResponse = {
  ok: boolean;
  queued: boolean;
  task?: {
    taskId: string;
    projectId: string;
    externalTaskId: string;
    identifier: string;
    repositoryId?: string;
    repositorySlug?: string;
    routed: boolean;
  };
};

export class AgentPlatformService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getWorkspaceSnapshot(workspaceSlug: string): Promise<AgentPlatformWorkspaceSnapshot> {
    const [agents, prompts, promptVersions, roles, promptBindings, secretKeys] = await Promise.all([
      this.list<AgentUserAgent>(workspaceSlug, "agent-agents"),
      this.list<AgentPrompt>(workspaceSlug, "agent-prompts"),
      this.list<AgentPromptVersion>(workspaceSlug, "agent-prompt-versions"),
      this.list<AgentRole>(workspaceSlug, "agent-roles"),
      this.list<AgentPromptBinding>(workspaceSlug, "agent-prompt-bindings"),
      this.list<AgentUserSecretKey>(workspaceSlug, "agent-user-secret-keys"),
    ]);

    return { agents, prompts, promptVersions, roles, promptBindings, secretKeys };
  }

  async getProjectSnapshot(workspaceSlug: string, projectId: string): Promise<AgentPlatformProjectSnapshot> {
    const [workerCards, projectWorkspaces, repositories] = await Promise.all([
      this.list<AgentWorkerCard>(workspaceSlug, "agent-worker-cards"),
      this.list<AgentProjectWorkspace>(workspaceSlug, "agent-project-workspaces"),
      this.list<AgentRepository>(workspaceSlug, "agent-repositories"),
    ]);

    return {
      workerCards,
      projectWorkspaces: projectWorkspaces.filter((item) => item.project === projectId),
      repositories: repositories.filter((item) => item.project === projectId),
    };
  }

  async createAgent(workspaceSlug: string, payload: Partial<AgentUserAgent>): Promise<AgentUserAgent> {
    return this.create(workspaceSlug, "agent-agents", payload);
  }

  async createPrompt(workspaceSlug: string, payload: Partial<AgentPrompt>): Promise<AgentPrompt> {
    return this.create(workspaceSlug, "agent-prompts", payload);
  }

  async createPromptVersion(workspaceSlug: string, payload: Partial<AgentPromptVersion>): Promise<AgentPromptVersion> {
    return this.create(workspaceSlug, "agent-prompt-versions", payload);
  }

  async createPromptBinding(workspaceSlug: string, payload: Partial<AgentPromptBinding>): Promise<AgentPromptBinding> {
    return this.create(workspaceSlug, "agent-prompt-bindings", payload);
  }

  async createRole(workspaceSlug: string, payload: Partial<AgentRole>): Promise<AgentRole> {
    return this.create(workspaceSlug, "agent-roles", payload);
  }

  async createSecretKey(workspaceSlug: string, payload: Partial<AgentUserSecretKey>): Promise<AgentUserSecretKey> {
    return this.create(workspaceSlug, "agent-user-secret-keys", payload);
  }

  async createWorkerCard(workspaceSlug: string, payload: Partial<AgentWorkerCard>): Promise<AgentWorkerCard> {
    return this.create(workspaceSlug, "agent-worker-cards", payload);
  }

  async createProjectWorkspace(
    workspaceSlug: string,
    payload: Partial<AgentProjectWorkspace>
  ): Promise<AgentProjectWorkspace> {
    return this.create(workspaceSlug, "agent-project-workspaces", payload);
  }

  async createRepository(workspaceSlug: string, payload: Partial<AgentRepository>): Promise<AgentRepository> {
    return this.create(workspaceSlug, "agent-repositories", payload);
  }

  async createRunIntent(workspaceSlug: string, payload: AgentRunIntentPayload): Promise<AgentRunIntentResponse> {
    return this.post(`/api/v1/workspaces/${workspaceSlug}/agent-runs/`, payload, { validateStatus: null })
      .then((response) => {
        if (response?.status >= 400) throw response?.data;
        return response?.data as AgentRunIntentResponse;
      })
      .catch((error) => {
        const agentError = error as AgentPlatformError;
        throw agentError.response?.data ?? error;
      });
  }

  private async list<T>(workspaceSlug: string, resource: string): Promise<T[]> {
    return this.get(`/api/v1/workspaces/${workspaceSlug}/${resource}/`, {}, { validateStatus: null })
      .then((response) => {
        if (response?.status === 401 || response?.status === 403) return [];
        if (response?.status >= 400) throw response?.data;
        return unwrapList<T>(response?.data);
      })
      .catch((error) => {
        const agentError = error as AgentPlatformError;
        if (agentError.response?.status === 401 || agentError.response?.status === 403) return [];
        throw agentError.response?.data ?? error;
      });
  }

  private async create<T>(workspaceSlug: string, resource: string, payload: object): Promise<T> {
    return this.post(`/api/v1/workspaces/${workspaceSlug}/${resource}/`, payload, { validateStatus: null })
      .then((response) => {
        if (response?.status >= 400) throw response?.data;
        return response?.data as T;
      })
      .catch((error) => {
        const agentError = error as AgentPlatformError;
        throw agentError.response?.data ?? error;
      });
  }
}

function unwrapList<T>(payload: ListResponse<T>): T[] {
  if (Array.isArray(payload)) return payload;
  return payload.results ?? [];
}
