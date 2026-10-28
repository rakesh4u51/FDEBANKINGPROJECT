#!/usr/bin/env bash
# Bootstrap a self-contained lab workspace for Module 5 Project 4.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$PROJECT_DIR/.." && pwd)"
WORKSPACE="$PROJECT_DIR/workspace"

# Prefer the copy bundled in this project (standalone clone); fall back to the
# shared sibling used by the full multi-project lab-VM tree.
if [[ -d "$PROJECT_DIR/fraud-detection-starter" ]]; then
  SOURCE="$PROJECT_DIR/fraud-detection-starter"
elif [[ -d "$REPO_ROOT/fraud-detection-starter" ]]; then
  SOURCE="$REPO_ROOT/fraud-detection-starter"
else
  echo "ERROR: fraud-detection-starter not found at $PROJECT_DIR/fraud-detection-starter or $REPO_ROOT/fraud-detection-starter"
  exit 1
fi

rm -rf "$WORKSPACE"
cp -r "$SOURCE" "$WORKSPACE"
mkdir -p "$WORKSPACE/.claude" "$WORKSPACE/reports" "$WORKSPACE/data"
cp "$SCRIPT_DIR/settings_template.json" "$WORKSPACE/.claude/settings.json"
cp "$SCRIPT_DIR/CLAUDE_md_template.md" "$WORKSPACE/CLAUDE.md"
cp -r "$SCRIPT_DIR/resources" "$WORKSPACE/lab_resources" 2>/dev/null || true
cp -r "$SCRIPT_DIR/evidence" "$WORKSPACE/evidence" 2>/dev/null || true
mkdir -p "$WORKSPACE/lab_resources"
cp -r "$SCRIPT_DIR/diagrams" "$WORKSPACE/lab_resources/diagrams" 2>/dev/null || true
echo "Seeded: CLAUDE.md, .claude/settings.json"
echo "Workspace ready: $WORKSPACE"
echo "Lab resources copied to workspace/lab_resources/"
echo "Evidence placeholders: workspace/evidence/placeholders/"
