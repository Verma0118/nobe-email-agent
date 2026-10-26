#!/bin/bash
# Installs the NOBE Email Agent for Claude Code:
#   - links this repo to ~/.claude/skills/nobe-email-agent (so `git pull` updates it)
#   - links the reviewer agent into ~/.claude/agents/
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

[ -f "$REPO/profile.json" ] || echo "no profile.json yet: the agent will set it up with you on first run"
mkdir -p "$REPO/targets"
chmod +x "$REPO/tools/"*.py

cat > "$BIN/nobe-email-agent" <<'SH'
#!/bin/bash
exec claude "/nobe-email-agent $*"
SH
chmod +x "$BIN/nobe-email-agent"
echo "installed command: $BIN/nobe-email-agent"

command -v claude >/dev/null || echo "WARNING: Claude Code not found. Install it first: https://claude.com/claude-code"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "WARNING: add $BIN to your PATH:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc";; esac
"$REPO/tests/run_tests.sh" >/dev/null && echo "self-test: pass" || echo "self-test: FAILED (run tests/run_tests.sh)"
echo "done. Type: nobe-email-agent"
