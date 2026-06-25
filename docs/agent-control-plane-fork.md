# Agent Control Plane Plane Fork

This fork is the self-hosted Plane source for Agent Control Plane.

## Baseline

- Upstream repository: `makeplane/plane`
- Fork repository: `michaelx1993/plane`
- Fork default branch: `preview`
- Current baseline commit: `53a323d559`
- Plane package version: `1.3.1`
- Required runtime ownership: self-hosted Plane source and deployment assets must come from this fork.

## Boundary

Plane remains the human task/project/state/review surface. It must not own agent runtime state.

Allowed responsibilities:

- Work item creation and review.
- Human state transitions.
- Project/team organization.
- Webhook delivery to Agent Control Plane.
- API/PAT access for Agent Control Plane sync and writeback.

Forbidden responsibilities:

- Agent dispatch, lease, retry, prompt release, run event, cost, or worker runtime state.
- Direct access to Agent Control Plane PostgreSQL.
- Worker token storage.

## Fork UX Customizations

This fork carries a small Plane web customization for the Agent Control Plane
self-hosted deployment:

- The workspace top navigation exposes a language switcher in the upper-right
  toolbar.
- The runtime language options are limited to English (`en`) and Simplified
  Chinese (`zh-CN`) through `BILINGUAL_LANGUAGES`.
- Profile preferences and Power-K language selection use the same bilingual
  option source, so the visible language choices stay consistent.
- The upstream "Star us on GitHub" top navigation link is removed from the
  self-hosted web UI.

Relevant implementation points:

- `packages/i18n/src/constants/language.ts`
- `packages/i18n/src/hooks/use-translation.ts`
- `apps/web/ce/components/navigations/language-switcher.tsx`
- `apps/web/ce/components/navigations/top-navigation-root.tsx`
- `apps/web/core/components/settings/profile/content/pages/preferences/language-and-timezone-list.tsx`
- `apps/web/core/components/power-k/ui/pages/preferences/languages-menu.tsx`

Validation commands:

```bash
pnpm --filter=@plane/i18n test
pnpm --filter=web test
pnpm --filter=web build
```

## Deployment Baseline

First production path is Docker Compose:

- `docker-compose.yml` is the production/staging compose baseline from upstream.
- `.env.example` is the environment template baseline.
- `setup.sh` remains the upstream bootstrap helper.

Before changing deployment behavior, run:

```bash
bash .github/acp-plane-fork-check.sh
```

Release smoke validates the fork baseline, Compose parseability, core Dockerfiles,
and the community build manifest with temporary local env files:

```bash
bash .github/acp-plane-release-smoke.sh
```

Release tag smoke validates the shared release tag before image or rollback
gates consume it. By default it is dry-run only; set `ACP_CREATE_GIT_TAG=true`
only in a controlled release shell:

```bash
ACP_RELEASE_TAG="plane-$(git rev-parse --short=12 HEAD)" \
bash .github/acp-plane-release-tag-smoke.sh
```

Image release dry-run validates that the community build manifest renders all
Plane service images under the fork-owned namespace/tag. Set
`PLANE_RELEASE_IMAGE_BUILD=true` only when intentionally building all Plane
service images:

```bash
DOCKERHUB_USER=michaelx1993 APP_RELEASE="$(git rev-parse --short=12 HEAD)" \
bash .github/acp-plane-release-image.sh
```

The `Release` workflow publishes the AIO image as `michaelxxx/plane:<version>`.
It builds the web frontend from this fork first, then injects that local
frontend image into the AIO build with `PLANE_FRONTEND_IMAGE`. The remaining AIO
runtime images still use the configured upstream Plane source release
(`plane_release`, default `v1.3.1`). This keeps fork-specific UI changes, such
as the bilingual top navigation, inside the published AIO image without
requiring a separate pushed frontend repository.

The `Release Plane Components` workflow publishes the multi-container Plane
application images from this fork for in-place Compose upgrades:

- `michaelxxx/plane-frontend:<version>`
- `michaelxxx/plane-backend:<version>`
- `michaelxxx/plane-admin:<version>`
- `michaelxxx/plane-space:<version>`
- `michaelxxx/plane-live:<version>`
- `michaelxxx/plane-proxy:<version>`

Use these component images when preserving the existing multi-container
deployment shape. PostgreSQL, Valkey/Redis, RabbitMQ, and MinIO remain community
infrastructure images.

Rollback smoke validates that the self-host community Compose file can be
rendered against a previous `APP_RELEASE` tag under a fork-owned image
namespace. It only checks application image rollback; database rollback remains
a separate backup/restore operation:

```bash
DOCKERHUB_USER=michaelx1993 PLANE_ROLLBACK_APP_RELEASE=previous \
bash .github/acp-plane-rollback-smoke.sh
```

This is a release configuration gate. It does not replace the real self-hosted
PAT/API/webhook/rate-limit smoke that must run against a live Plane deployment.

## Agent Control Plane Backlog

### P0: Agent Platform Source Tables

Plane owns the editable configuration source of truth for the first Agent
Platform slice. Agent Control Plane owns runtime projections, dispatch, lease,
retry, run events, and worker state.

Source tables added under the Plane `db` app:

- `agent_user_agents`: user/workspace-level agent definitions.
- `agent_prompts`: prompt metadata and type (`agent`, `project`, `role`,
  `playbook_task`, `business_system`).
- `agent_prompt_versions`: immutable prompt bodies and configured effective
  versions.
- `agent_prompt_bindings`: ordered prompt composition for an agent.
- `agent_roles`: reusable role definitions.
- `agent_worker_cards`: selectable worker cards for real-machine execution.
- `agent_project_workspaces`: project local workspace and status/progress/meta
  document paths.
- `agent_repositories`: registered repositories used by project workspaces.
- `agent_config_outbox`: monotonic workspace-scoped change feed consumed by
  Agent Control Plane.

External API endpoints use existing Plane API key auth:

```text
GET  /api/v1/workspaces/{slug}/agent-config-outbox/?after_id=0&limit=100
GET  /api/v1/workspaces/{slug}/agent-agents/
POST /api/v1/workspaces/{slug}/agent-agents/
GET  /api/v1/workspaces/{slug}/agent-prompts/
POST /api/v1/workspaces/{slug}/agent-prompts/
GET  /api/v1/workspaces/{slug}/agent-prompt-versions/
POST /api/v1/workspaces/{slug}/agent-prompt-versions/
GET  /api/v1/workspaces/{slug}/agent-roles/
POST /api/v1/workspaces/{slug}/agent-roles/
GET  /api/v1/workspaces/{slug}/agent-prompt-bindings/
POST /api/v1/workspaces/{slug}/agent-prompt-bindings/
GET  /api/v1/workspaces/{slug}/agent-worker-cards/
POST /api/v1/workspaces/{slug}/agent-worker-cards/
GET  /api/v1/workspaces/{slug}/agent-project-workspaces/
POST /api/v1/workspaces/{slug}/agent-project-workspaces/
GET  /api/v1/workspaces/{slug}/agent-repositories/
POST /api/v1/workspaces/{slug}/agent-repositories/
```

Each create/update/delete writes one `agent_config_outbox` record in the same
database transaction. ACP must poll the outbox by `after_id` and persist its own
last cursor per workspace.

### P1: Repo Field

Current MVP uses `repo:<slug>` labels because Plane custom properties are not reliable enough in the validated self-host path.

Backlog:

- Add a first-class repository field to work items.
- Preserve the `repo:<slug>` label fallback for migration.
- Expose repository field through API and webhook payloads.
- Add UI affordance on work item detail.

### P1: Agent Status Embed

Backlog:

- Show linked Agent Control Plane run summary on work item detail.
- Show latest Progress / Workpad URL.
- Show active run status: Claimed / Running / Completed / Failed.
- Keep the embedded view read-only; writes still happen through Control Plane APIs.

### P1: API/Webhook Regression

Regression surface:

- Work item list/get/update.
- State transition writeback.
- Comment writeback.
- Work item created/updated webhooks.
- Comment webhooks.
- Rate-limit behavior and retry metadata.

## Release Rule

Any Agent Control Plane-specific Plane change must:

- Keep this document updated.
- Pass `.github/acp-plane-fork-check.sh`.
- Pass `.github/acp-plane-release-smoke.sh`.
- Pass GitHub Actions `Agent Control Plane Fork Gate`.
- Pass GitHub Actions `Agent Control Plane Release Smoke` when deployment files change.
- Avoid storing Agent Control Plane secrets in this repository.
