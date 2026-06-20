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

Image release dry-run validates that the community build manifest renders all
Plane service images under the fork-owned namespace/tag. Set
`PLANE_RELEASE_IMAGE_BUILD=true` only when intentionally building all Plane
service images:

```bash
DOCKERHUB_USER=michaelx1993 APP_RELEASE="$(git rev-parse --short=12 HEAD)" \
bash .github/acp-plane-release-image.sh
```

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
