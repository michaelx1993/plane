#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fail() {
  echo "acp-plane-component-release-smoke: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing required file: $path"
}

require_file .github/workflows/release-components.yml
require_file apps/web/Dockerfile.web
require_file apps/api/Dockerfile.api
require_file apps/admin/Dockerfile.admin
require_file apps/space/Dockerfile.space
require_file apps/live/Dockerfile.live
require_file apps/proxy/Dockerfile.ce

images=(
  plane-frontend
  plane-backend
  plane-admin
  plane-space
  plane-live
  plane-proxy
)

for image in "${images[@]}"; do
  grep -q "image: ${image}" .github/workflows/release-components.yml ||
    fail "missing component image in release workflow: ${image}"
done

grep -q 'tags:' .github/workflows/release-components.yml ||
  fail "component release workflow must support tag-triggered releases"

grep -q 'docker push' .github/workflows/release-components.yml ||
  fail "component release workflow must push component images"

grep -q 'dockerfile: apps/api/Dockerfile.api' .github/workflows/release-components.yml ||
  fail "backend Dockerfile path must be relative to the repository root"

grep -q 'dockerfile: apps/proxy/Dockerfile.ce' .github/workflows/release-components.yml ||
  fail "proxy Dockerfile path must be relative to the repository root"

echo "acp-plane-component-release-smoke: ok"
