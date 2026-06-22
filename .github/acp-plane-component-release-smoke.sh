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

if ! grep -q 'docker push' .github/workflows/release-components.yml &&
  ! grep -q 'push: true' .github/workflows/release-components.yml; then
  fail "component release workflow must push component images"
fi

grep -q 'docker/setup-qemu-action' .github/workflows/release-components.yml ||
  fail "component release workflow must set up QEMU for cross-platform builds"

grep -q 'docker/setup-buildx-action' .github/workflows/release-components.yml ||
  fail "component release workflow must set up Docker Buildx"

grep -q 'docker/build-push-action' .github/workflows/release-components.yml ||
  fail "component release workflow must use Docker Buildx publishing"

grep -q 'platforms: linux/amd64,linux/arm64' .github/workflows/release-components.yml ||
  fail "component release workflow must publish amd64 and arm64 images where supported"

grep -q 'platforms: linux/amd64' .github/workflows/release-components.yml ||
  fail "component release workflow must allow component-specific platform overrides"

grep -q 'dockerfile: apps/api/Dockerfile.api' .github/workflows/release-components.yml ||
  fail "backend Dockerfile path must be relative to the repository root"

grep -q 'dockerfile: apps/proxy/Dockerfile.ce' .github/workflows/release-components.yml ||
  fail "proxy Dockerfile path must be relative to the repository root"

echo "acp-plane-component-release-smoke: ok"
