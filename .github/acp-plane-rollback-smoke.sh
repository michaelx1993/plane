#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fail() {
  echo "acp-plane-rollback-smoke: $*" >&2
  exit 1
}

require_command() {
  local command="$1"
  command -v "$command" >/dev/null 2>&1 || fail "missing command: $command"
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing required file: $path"
}

require_command docker
require_file deployments/cli/community/docker-compose.yml

DOCKERHUB_USER="${DOCKERHUB_USER:-michaelx1993}"
APP_RELEASE="${PLANE_ROLLBACK_APP_RELEASE:-${APP_RELEASE:-previous}}"

export DOCKERHUB_USER APP_RELEASE

config_output="$(docker compose -f deployments/cli/community/docker-compose.yml config)"

images=(
  "${DOCKERHUB_USER}/plane-frontend:${APP_RELEASE}"
  "${DOCKERHUB_USER}/plane-space:${APP_RELEASE}"
  "${DOCKERHUB_USER}/plane-admin:${APP_RELEASE}"
  "${DOCKERHUB_USER}/plane-live:${APP_RELEASE}"
  "${DOCKERHUB_USER}/plane-backend:${APP_RELEASE}"
  "${DOCKERHUB_USER}/plane-proxy:${APP_RELEASE}"
)

for image in "${images[@]}"; do
  grep -q "image: ${image}" <<<"$config_output" || fail "missing rollback image: ${image}"
done

cat <<EOF
rollback_smoke=passed
rollback_image_namespace=${DOCKERHUB_USER}
rollback_image_tag=${APP_RELEASE}
database_rollback=not_performed
EOF
