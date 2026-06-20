#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "acp-plane-fork-check: $*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "missing required file: $1"
}

require_file package.json
require_file pnpm-workspace.yaml
require_file pnpm-lock.yaml
require_file docker-compose.yml
require_file .env.example
require_file setup.sh
require_file docs/agent-control-plane-fork.md

node <<'NODE'
const fs = require("node:fs");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
if (pkg.name !== "plane") {
  throw new Error(`expected package name plane, got ${pkg.name}`);
}
if (pkg.version !== "1.3.1") {
  throw new Error(`expected Plane baseline version 1.3.1, got ${pkg.version}`);
}
if (!String(pkg.packageManager || "").startsWith("pnpm@")) {
  throw new Error("packageManager must use pnpm");
}
if (!pkg.engines || !String(pkg.engines.node || "").includes("22.18.0")) {
  throw new Error("Node engine baseline must mention >=22.18.0");
}
NODE

grep -q "Current baseline commit: \`53a323d559\`" docs/agent-control-plane-fork.md \
  || fail "fork doc must record current baseline commit"

grep -q "repo:<slug>" docs/agent-control-plane-fork.md \
  || fail "fork doc must record repo label fallback"

grep -q "Agent Control Plane Backlog" docs/agent-control-plane-fork.md \
  || fail "fork doc must include Agent Control Plane backlog"

SECRET_SCAN_PATHS=(docs .github/acp-plane-fork-check.sh .env.example)
if grep -R --line-number --exclude-dir=.git -E 'sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9_]{20,}|Bearer [A-Za-z0-9._~+/-]{20,}' "${SECRET_SCAN_PATHS[@]}" >/tmp/acp-plane-secret-scan.txt; then
  cat /tmp/acp-plane-secret-scan.txt >&2
  fail "high-confidence secret pattern found"
fi

echo "acp-plane-fork-check: ok"
