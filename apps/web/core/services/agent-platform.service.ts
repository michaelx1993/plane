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
  prompt_count?: number;
  prompt_stack?: AgentPromptStackItem[];
};

export type AgentPromptStackItem = {
  id: string;
  prompt: string;
  prompt_key: string;
  prompt_name: string;
  prompt_scope: AgentPromptScope;
  prompt_kind: AgentPromptKind;
  prompt_status: string;
  version_policy: AgentPromptVersionPolicy;
  pinned_version: string | null;
  resolved_version: number;
  role: string | null;
  role_key: string;
  slot: string;
  sort_order: number;
  is_required: boolean;
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

export type AgentWorkDirectory = {
  id: string;
  key: string;
  name: string;
  description: string;
  root_path: string;
  default_worker_card: string | null;
  default_worker_key?: string;
  worktree_strategy: string;
  branch_policy: Record<string, unknown>;
  prd_path: string;
  status_path: string;
  progress_path: string;
  repository_count?: number;
  mount_count?: number;
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

export type AgentWorkDirectoryRepository = {
  id: string;
  work_directory: string;
  repository: string;
  repository_key?: string;
  repository_name?: string;
  repository_url?: string;
  relative_path: string;
  default_branch: string;
  worktree_strategy: string;
  sort_order: number;
  is_required: boolean;
  is_active: boolean;
};

export type AgentWorkerMount = {
  id: string;
  work_directory: string;
  work_directory_key?: string;
  worker_card: string;
  worker_key?: string;
  worker_name?: string;
  local_path: string;
  is_default: boolean;
  is_active: boolean;
};

export type AgentProjectDefault = {
  id: string;
  project: string;
  project_identifier?: string;
  work_directory: string | null;
  work_directory_key?: string;
  worker_card: string | null;
  worker_key?: string;
  is_active: boolean;
};

export type AgentTaskWorkDirectoryOverride = {
  id: string;
  issue: string;
  issue_sequence_id?: number;
  work_directory: string | null;
  work_directory_key?: string;
  worker_card: string | null;
  worker_key?: string;
  target_branch: string;
  is_active: boolean;
};

export type AgentTaskContextDocumentType = "prd" | "status";

export type AgentTaskContextDocument = {
  id: string;
  workspace: string;
  issue: string;
  issue_sequence_id?: number;
  project: string;
  document_type: AgentTaskContextDocumentType;
  path: string;
  title: string;
  body: string;
  body_format: string;
  version: number;
  version_count: number;
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentTaskProgressEntry = {
  id: string;
  workspace: string;
  issue: string;
  issue_sequence_id?: number;
  project: string;
  entry_type: string;
  source: string;
  body: string;
  summary: string;
  author: string | null;
  node_key: string;
  run_id: string;
  occurred_at: string;
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentTaskWorkflowNode = {
  id: string;
  workspace: string;
  workflow_instance: string;
  issue: string;
  issue_sequence_id?: number;
  key: string;
  name: string;
  node_type: string;
  owner_type: string;
  mode: string;
  status: string;
  sort_order: number;
  main_exits: string[];
  assigned_agent: string | null;
  assigned_agent_key?: string;
  assigned_agent_name?: string;
  started_at: string | null;
  completed_at: string | null;
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentTaskWorkflowInstance = {
  id: string;
  workspace: string;
  issue: string;
  issue_sequence_id?: number;
  project: string;
  template_key: string;
  template_version: number;
  name: string;
  status: string;
  active_node: string | null;
  active_node_key?: string;
  active_node_name?: string;
  default_agent: string | null;
  default_agent_key?: string;
  nodes: AgentTaskWorkflowNode[];
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentTaskContextSnapshot = {
  source: string;
  workspaceSlug: string;
  project: {
    id: string;
    identifier: string;
    name: string;
  };
  task: {
    id: string;
    identifier: string;
    title: string;
    state: {
      id?: string;
      name?: string;
      group?: string;
    } | null;
  };
  documents: {
    prd: AgentTaskContextDocument | null;
    status: AgentTaskContextDocument | null;
  };
  progressEntries: AgentTaskProgressEntry[];
  renderedProgress: string;
  humanComments: Array<{
    id: string;
    body: string;
    html: string;
    actor: string | null;
    createdAt: string;
  }>;
  workDirectory: {
    source: string;
    projectId: string;
    workItemId: string | null;
    workDirectory: {
      id: string;
      key: string;
      name: string;
      rootPath: string;
      worktreeStrategy: string;
      branchPolicy: Record<string, unknown>;
      prdPath: string;
      statusPath: string;
      progressPath: string;
    } | null;
    worker: {
      id: string;
      key: string;
      name: string;
      endpoint: string;
    } | null;
    mount: {
      id: string;
      localPath: string;
      isDefault: boolean;
    } | null;
    repositories: Array<{
      id: string;
      key: string;
      provider: string;
      name: string;
      fullName: string;
      url: string;
      relativePath: string;
      defaultBranch: string;
      worktreeStrategy: string;
      isRequired: boolean;
    }>;
  };
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
  workDirectories: AgentWorkDirectory[];
  workDirectoryRepositories: AgentWorkDirectoryRepository[];
  workerMounts: AgentWorkerMount[];
  projectDefaults: AgentProjectDefault[];
  taskWorkDirectoryOverrides: AgentTaskWorkDirectoryOverride[];
  projectWorkspaces: AgentProjectWorkspace[];
  repositories: AgentRepository[];
};

export type AgentPlatformWorkDirectorySnapshot = {
  workerCards: AgentWorkerCard[];
  workDirectories: AgentWorkDirectory[];
  repositories: AgentRepository[];
  workDirectoryRepositories: AgentWorkDirectoryRepository[];
  workerMounts: AgentWorkerMount[];
  projectDefaults: AgentProjectDefault[];
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
    const [
      workerCards,
      workDirectories,
      repositories,
      workDirectoryRepositories,
      workerMounts,
      projectDefaults,
      taskWorkDirectoryOverrides,
      projectWorkspaces,
    ] = await Promise.all([
      this.list<AgentWorkerCard>(workspaceSlug, "agent-worker-cards"),
      this.list<AgentWorkDirectory>(workspaceSlug, "agent-work-directories"),
      this.list<AgentRepository>(workspaceSlug, "agent-repositories"),
      this.list<AgentWorkDirectoryRepository>(workspaceSlug, "agent-work-directory-repositories"),
      this.list<AgentWorkerMount>(workspaceSlug, "agent-worker-mounts"),
      this.list<AgentProjectDefault>(workspaceSlug, "agent-project-defaults"),
      this.list<AgentTaskWorkDirectoryOverride>(workspaceSlug, "agent-task-work-directory-overrides"),
      this.list<AgentProjectWorkspace>(workspaceSlug, "agent-project-workspaces"),
    ]);

    return {
      workerCards,
      workDirectories,
      workDirectoryRepositories,
      workerMounts,
      projectDefaults: projectDefaults.filter((item) => item.project === projectId),
      taskWorkDirectoryOverrides,
      projectWorkspaces: projectWorkspaces.filter((item) => item.project === projectId),
      repositories: repositories.filter((item) => item.project === projectId || item.project === null),
    };
  }

  async getWorkDirectorySnapshot(workspaceSlug: string): Promise<AgentPlatformWorkDirectorySnapshot> {
    const [workerCards, workDirectories, repositories, workDirectoryRepositories, workerMounts, projectDefaults] =
      await Promise.all([
        this.list<AgentWorkerCard>(workspaceSlug, "agent-worker-cards"),
        this.list<AgentWorkDirectory>(workspaceSlug, "agent-work-directories"),
        this.list<AgentRepository>(workspaceSlug, "agent-repositories"),
        this.list<AgentWorkDirectoryRepository>(workspaceSlug, "agent-work-directory-repositories"),
        this.list<AgentWorkerMount>(workspaceSlug, "agent-worker-mounts"),
        this.list<AgentProjectDefault>(workspaceSlug, "agent-project-defaults"),
      ]);

    return { workerCards, workDirectories, repositories, workDirectoryRepositories, workerMounts, projectDefaults };
  }

  async createAgent(workspaceSlug: string, payload: Partial<AgentUserAgent>): Promise<AgentUserAgent> {
    return this.create(workspaceSlug, "agent-agents", payload);
  }

  async updateAgent(workspaceSlug: string, agentId: string, payload: Partial<AgentUserAgent>): Promise<AgentUserAgent> {
    return this.update(workspaceSlug, "agent-agents", agentId, payload);
  }

  async createPrompt(workspaceSlug: string, payload: Partial<AgentPrompt>): Promise<AgentPrompt> {
    return this.create(workspaceSlug, "agent-prompts", payload);
  }

  async updatePrompt(workspaceSlug: string, promptId: string, payload: Partial<AgentPrompt>): Promise<AgentPrompt> {
    return this.update(workspaceSlug, "agent-prompts", promptId, payload);
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

  async updateWorkerCard(
    workspaceSlug: string,
    workerCardId: string,
    payload: Partial<AgentWorkerCard>
  ): Promise<AgentWorkerCard> {
    return this.update(workspaceSlug, "agent-worker-cards", workerCardId, payload);
  }

  async createWorkDirectory(workspaceSlug: string, payload: Partial<AgentWorkDirectory>): Promise<AgentWorkDirectory> {
    return this.create(workspaceSlug, "agent-work-directories", payload);
  }

  async updateWorkDirectory(
    workspaceSlug: string,
    workDirectoryId: string,
    payload: Partial<AgentWorkDirectory>
  ): Promise<AgentWorkDirectory> {
    return this.update(workspaceSlug, "agent-work-directories", workDirectoryId, payload);
  }

  async createWorkDirectoryRepository(
    workspaceSlug: string,
    payload: Partial<AgentWorkDirectoryRepository>
  ): Promise<AgentWorkDirectoryRepository> {
    return this.create(workspaceSlug, "agent-work-directory-repositories", payload);
  }

  async createWorkerMount(workspaceSlug: string, payload: Partial<AgentWorkerMount>): Promise<AgentWorkerMount> {
    return this.create(workspaceSlug, "agent-worker-mounts", payload);
  }

  async createProjectDefault(
    workspaceSlug: string,
    payload: Partial<AgentProjectDefault>
  ): Promise<AgentProjectDefault> {
    return this.create(workspaceSlug, "agent-project-defaults", payload);
  }

  async updateProjectDefault(
    workspaceSlug: string,
    projectDefaultId: string,
    payload: Partial<AgentProjectDefault>
  ): Promise<AgentProjectDefault> {
    return this.update(workspaceSlug, "agent-project-defaults", projectDefaultId, payload);
  }

  async createTaskWorkDirectoryOverride(
    workspaceSlug: string,
    payload: Partial<AgentTaskWorkDirectoryOverride>
  ): Promise<AgentTaskWorkDirectoryOverride> {
    return this.create(workspaceSlug, "agent-task-work-directory-overrides", payload);
  }

  async updateTaskWorkDirectoryOverride(
    workspaceSlug: string,
    taskOverrideId: string,
    payload: Partial<AgentTaskWorkDirectoryOverride>
  ): Promise<AgentTaskWorkDirectoryOverride> {
    return this.update(workspaceSlug, "agent-task-work-directory-overrides", taskOverrideId, payload);
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

  async getTaskContextSnapshot(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    workerId?: string | null
  ): Promise<AgentTaskContextSnapshot | null> {
    const params = new URLSearchParams({
      project_id: projectId,
      work_item_id: issueId,
    });
    if (workerId) params.set("worker_id", workerId);

    return this.get(
      `/api/v1/workspaces/${workspaceSlug}/agent-task-context-snapshot/?${params.toString()}`,
      {},
      {
        validateStatus: null,
      }
    )
      .then((response) => {
        if (response?.status === 401 || response?.status === 403 || response?.status === 404) return null;
        if (response?.status >= 400) throw response?.data;
        return response?.data as AgentTaskContextSnapshot;
      })
      .catch((error) => {
        const agentError = error as AgentPlatformError;
        if (
          agentError.response?.status === 401 ||
          agentError.response?.status === 403 ||
          agentError.response?.status === 404
        ) {
          return null;
        }
        throw agentError.response?.data ?? error;
      });
  }

  async listTaskWorkflowInstances(workspaceSlug: string, issueId: string): Promise<AgentTaskWorkflowInstance[]> {
    return this.get(
      `/api/v1/workspaces/${workspaceSlug}/agent-task-workflow-instances/?issue_id=${encodeURIComponent(issueId)}`,
      {},
      { validateStatus: null }
    )
      .then((response) => {
        if (response?.status === 401 || response?.status === 403) return [];
        if (response?.status >= 400) throw response?.data;
        return unwrapList<AgentTaskWorkflowInstance>(response?.data);
      })
      .catch((error) => {
        const agentError = error as AgentPlatformError;
        if (agentError.response?.status === 401 || agentError.response?.status === 403) return [];
        throw agentError.response?.data ?? error;
      });
  }

  async createTaskContextDocument(
    workspaceSlug: string,
    payload: Partial<AgentTaskContextDocument>
  ): Promise<AgentTaskContextDocument> {
    return this.create(workspaceSlug, "agent-task-context-documents", payload);
  }

  async updateTaskContextDocument(
    workspaceSlug: string,
    documentId: string,
    payload: Partial<AgentTaskContextDocument>
  ): Promise<AgentTaskContextDocument> {
    return this.update(workspaceSlug, "agent-task-context-documents", documentId, payload);
  }

  async createTaskProgressEntry(
    workspaceSlug: string,
    payload: Partial<AgentTaskProgressEntry>
  ): Promise<AgentTaskProgressEntry> {
    return this.create(workspaceSlug, "agent-task-progress-entries", payload);
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

  private async update<T>(workspaceSlug: string, resource: string, id: string, payload: object): Promise<T> {
    return this.patch(`/api/v1/workspaces/${workspaceSlug}/${resource}/${id}/`, payload, { validateStatus: null })
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
