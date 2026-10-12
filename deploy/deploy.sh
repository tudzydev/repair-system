#!/usr/bin/env bash
set -euo pipefail

repair_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repair_root"
repair_deploy_dir="${DEPLOY_DIR:-/opt/repair-system}"
if [[ "$repair_deploy_dir" != /* ]]; then
  echo 'DEPLOY_DIR must be an absolute path.' >&2
  exit 1
fi
repair_env_file="$repair_deploy_dir/server.env"
if [[ ! -r "$repair_env_file" ]]; then
  echo "Create $repair_env_file from deploy/server.env.example before deploying." >&2
  exit 1
fi

docker info >/dev/null
docker compose version
docker compose --env-file "$repair_env_file" -f compose.yaml config --quiet
repair_revision="${GITHUB_SHA:-$(git rev-parse HEAD)}"
if [[ ! "$repair_revision" =~ ^[0-9a-f]{40}$ ]]; then
  echo 'Deployment requires a full Git commit SHA.' >&2
  exit 1
fi
export REPAIR_IMAGE="school-repair:$repair_revision"

docker build --tag "$REPAIR_IMAGE" .
docker run --rm --entrypoint python "$REPAIR_IMAGE" -m unittest discover -s tests -v

# Keep the Caddy bind mount outside the runner's checkout directory.
mkdir -p "$repair_deploy_dir/deploy"
install -m 644 compose.yaml "$repair_deploy_dir/compose.yaml"
install -m 644 deploy/Caddyfile "$repair_deploy_dir/deploy/Caddyfile"
docker compose --project-name repair-system \
  --project-directory "$repair_deploy_dir" \
  --env-file "$repair_env_file" -f "$repair_deploy_dir/compose.yaml" \
  up -d --no-build --force-recreate --wait --wait-timeout 180
printf 'Deployed commit %s\n' "$repair_revision"
