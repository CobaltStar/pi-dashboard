#!/bin/bash
# Polling deploy script — lives at ~/pi-dashboard/deploy/pull-deploy.sh on the Pi.
# Run every minute by cron (installed by setup-on-pi.sh). Checks GitHub for
# new commits on main and only rebuilds if something actually changed.
#
# Manual usage: bash deploy/pull-deploy.sh

set -e

WORK_TREE="$HOME/pi-dashboard"
LOG_FILE="$WORK_TREE/deploy/pull-deploy.log"
BRANCH="main"

cd "$WORK_TREE"

{
  echo "==> $(date -Iseconds) checking for updates"

  git fetch origin "$BRANCH" --quiet

  LOCAL=$(git rev-parse "$BRANCH")
  REMOTE=$(git rev-parse "origin/$BRANCH")

  if [ "$LOCAL" = "$REMOTE" ]; then
    echo "==> up to date ($LOCAL), nothing to do"
    exit 0
  fi

  echo "==> new commit(s) found: $LOCAL -> $REMOTE"
  git reset --hard "origin/$BRANCH"

  # .env holds real secrets and lives only on the Pi, never in git — make sure
  # it exists (first deploy) before compose tries to read it.
  if [ ! -f .env ]; then
    echo "==> no .env found, copying from .env.example — edit it with real credentials!"
    cp .env.example .env
  fi

  echo "==> rebuilding and restarting container"
  docker compose up -d --build

  echo "==> deploy complete ($REMOTE)"
} >> "$LOG_FILE" 2>&1
