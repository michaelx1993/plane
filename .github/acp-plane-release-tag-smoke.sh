#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fail() {
  echo "acp-plane-release-tag-smoke: $*" >&2
  exit 1
}

COMPONENT="${ACP_RELEASE_COMPONENT:-plane}"
COMMIT_SHA="${GITHUB_SHA:-$(git rev-parse HEAD)}"
SHORT_SHA="$(git rev-parse --short=12 "$COMMIT_SHA")"
TAG="${ACP_RELEASE_TAG:-${COMPONENT}-${SHORT_SHA}}"
DOCKERHUB_USER="${DOCKERHUB_USER:-michaelx1993}"

case "$TAG" in
  *[[:space:]]* | "" | latest | stable | local)
    fail "invalid tag: ${TAG}"
    ;;
esac

if [[ ! "$TAG" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]]; then
  fail "tag must match OCI and git-safe pattern: ${TAG}"
fi

if [[ "${ACP_CREATE_GIT_TAG:-false}" == "true" ]]; then
  if git rev-parse "$TAG" >/dev/null 2>&1; then
    fail "tag already exists: ${TAG}"
  fi
  git tag -a "$TAG" -m "Release ${COMPONENT} ${TAG}" "$COMMIT_SHA"
  created=true
else
  created=false
fi

cat <<EOF
release_tag_smoke=passed
component=${COMPONENT}
tag=${TAG}
commit=${COMMIT_SHA}
image_namespace=${DOCKERHUB_USER}
image_tag=${TAG}
created=${created}
EOF
