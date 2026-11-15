#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$repo_dir/scripts/check_repo.py"
bash -n "$repo_dir/scripts/build.sh" "$repo_dir/scripts/check.sh" "$repo_dir/docker/entrypoint.sh"
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
    docker compose -f "$repo_dir/docker/compose.yaml" config --quiet
else
    printf 'Docker Compose unavailable; skipped Compose validation.\n'
fi
