#!/bin/bash
# Run this ONCE on the Pi to set up pull-from-GitHub deploy.
# Usage: ssh into the Pi, then: bash setup-on-pi.sh <github-repo-url>
# Example: bash setup-on-pi.sh git@github.com:you/pi-dashboard.git

set -e

REPO_URL="$1"
WORK_TREE="$HOME/pi-dashboard"

if [ -z "$REPO_URL" ]; then
  echo "Usage: bash setup-on-pi.sh <github-repo-url>"
  exit 1
fi

if [ -d "$WORK_TREE/.git" ]; then
  echo "==> $WORK_TREE already a git repo, skipping clone"
else
  echo "==> Cloning $REPO_URL into $WORK_TREE"
  git clone "$REPO_URL" "$WORK_TREE"
fi

chmod +x "$WORK_TREE/deploy/pull-deploy.sh"

CRON_LINE="* * * * * $WORK_TREE/deploy/pull-deploy.sh"
( crontab -l 2>/dev/null | grep -vF "pull-deploy.sh" ; echo "$CRON_LINE" ) | crontab -

echo ""
echo "Cron job installed — checks GitHub every minute and deploys on change."
echo "Logs at $WORK_TREE/deploy/pull-deploy.log"
echo ""
echo "On your DEV MACHINE:"
echo "  git remote add origin $REPO_URL   # if not already set"
echo "  git push origin main"
echo ""
echo "The Pi will pick up the change within a minute and rebuild automatically."
