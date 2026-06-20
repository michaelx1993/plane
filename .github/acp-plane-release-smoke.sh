#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fail() {
  echo "acp-plane-release-smoke: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing required file: $path"
}

require_command() {
  local command="$1"
  command -v "$command" >/dev/null 2>&1 || fail "missing command: $command"
}

managed_files=()

create_if_missing() {
  local path="$1"
  local body="$2"

  if [[ -e "$path" ]]; then
    return 0
  fi

  mkdir -p "$(dirname "$path")"
  printf "%s\n" "$body" >"$path"
  managed_files+=("$path")
}

cleanup() {
  local path
  for path in "${managed_files[@]}"; do
    rm -f "$path"
  done
}
trap cleanup EXIT

require_command docker
require_file .github/acp-plane-fork-check.sh
require_file docs/agent-control-plane-fork.md
require_file docker-compose.yml
require_file deployments/cli/community/build.yml
require_file deployments/cli/community/docker-compose.yml
require_file apps/web/Dockerfile.web
require_file apps/admin/Dockerfile.admin
require_file apps/space/Dockerfile.space
require_file apps/live/Dockerfile.live
require_file apps/api/Dockerfile.api
require_file apps/proxy/Dockerfile.ce

bash .github/acp-plane-fork-check.sh

create_if_missing .env "POSTGRES_USER=plane
POSTGRES_DB=plane
POSTGRES_PASSWORD=plane
RABBITMQ_USER=plane
RABBITMQ_PASSWORD=plane
RABBITMQ_VHOST=plane
AWS_ACCESS_KEY_ID=plane
AWS_SECRET_ACCESS_KEY=plane
AWS_S3_BUCKET_NAME=uploads
FILE_SIZE_LIMIT=5242880
LISTEN_HTTP_PORT=8080
LISTEN_HTTPS_PORT=8443"

create_if_missing apps/api/.env "DATABASE_URL=postgresql://plane:plane@plane-db:5432/plane
REDIS_URL=redis://plane-redis:6379
AMQP_URL=amqp://plane:plane@plane-mq:5672/plane
SECRET_KEY=plane-local-release-smoke
WEB_URL=http://localhost:8080"

docker compose -f docker-compose.yml config --quiet
docker compose -f deployments/cli/community/build.yml config --quiet

grep -q 'image: ${DOCKERHUB_USER:-local}/plane-frontend:${APP_RELEASE:-latest}' deployments/cli/community/build.yml ||
  fail "community build manifest must keep local image namespace fallback"

echo "acp-plane-release-smoke: ok"
