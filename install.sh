#!/bin/bash
# Installs the NOBE Email Agent for Claude Code:
#   - links this folder to ~/.claude/skills/nobe-email-agent
#   - links the reviewer agent into ~/.claude/agents/
#   - asks for the shared brain key (once) and saves it to brain.key
#   - adds a `nobe-email-agent` terminal command in ~/.local/bin
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$HOME/.claude/skills"; AGENTS="$HOME/.claude/agents"; BIN="$HOME/.local/bin"
mkdir -p "$SKILLS" "$AGENTS" "$BIN"

link() {  # link SRC DEST, refusing to clobber a real file or folder
  if [ -e "$2" ] && [ ! -L "$2" ]; then echo "refusing: $2 exists and is not a link"; exit 1; fi
  ln -sfn "$1" "$2"; echo "linked $2"
}
link "$REPO" "$SKILLS/nobe-email-agent"
link "$REPO/agents/nobe-email-reviewer.md" "$AGENTS/nobe-email-reviewer.md"
mkdir -p "$REPO/targets"
chmod +x "$REPO/tools/"*.py "$REPO/tests/"*.sh "$REPO/get.sh"

if [ ! -s "$REPO/brain.key" ]; then
  echo
  echo "The shared brain makes sure no one at NOBE emails the same person twice."
  read -r -p "Paste the brain key you got from the owner (Enter to skip for now): " key || key=""
  if [ -n "$key" ]; then
    printf '%s\n' "$key" > "$REPO/brain.key"; chmod 600 "$REPO/brain.key"; echo "saved brain.key"
  else
    echo "skipped: drafting stays blocked until you add it (run ./install.sh again)"
  fi
fi

cat > "$BIN/nobe-email-agent" <<'SH'
#!/bin/bash
exec claude "/nobe-email-agent $*"
SH
chmod +x "$BIN/nobe-email-agent"
echo "installed command: $BIN/nobe-email-agent"

command -v claude >/dev/null || echo "WARNING: Claude Code not found. Install it first: https://claude.com/claude-code"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "WARNING: add $BIN to your PATH:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc";; esac
"$REPO/tests/run_tests.sh" >/dev/null 2>&1 && echo "self-test: pass" || echo "self-test: FAILED (run tests/run_tests.sh)"
[ -s "$REPO/brain.key" ] && { python3 "$REPO/tools/brain.py" sync | tail -1 || true; }
echo "done. Type: nobe-email-agent"
