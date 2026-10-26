#!/bin/bash
# Install or update the NOBE Email Agent without git or a GitHub account.
#   curl -fsSL https://raw.githubusercontent.com/Verma0118/nobe-email-agent/main/get.sh | bash
# Downloads the latest code into ~/nobe-email-agent, keeps your profile.json, brain.key, and
# targets/, then runs install.sh. Run the same command again any time to update.
set -euo pipefail
DIR="${NOBE_AGENT_DIR:-$HOME/nobe-email-agent}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

if [ -d "$DIR/.git" ]; then
  echo "git checkout found, updating with git pull"; git -C "$DIR" pull -q
else
  curl -fsSL https://github.com/Verma0118/nobe-email-agent/archive/refs/heads/main.tar.gz | tar xz -C "$TMP"
  mkdir -p "$DIR"
  for keep in profile.json brain.key targets; do
    [ -e "$DIR/$keep" ] && mv "$DIR/$keep" "$TMP/"
  done
  find "$DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -R "$TMP/nobe-email-agent-main/." "$DIR/"
  for keep in profile.json brain.key targets; do
    [ -e "$TMP/$keep" ] && mv "$TMP/$keep" "$DIR/"
  done
  echo "downloaded latest into $DIR"
fi
"$DIR/install.sh" < /dev/tty
