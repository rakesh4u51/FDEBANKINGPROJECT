#!/usr/bin/env python3
"""Cross-platform workspace bootstrap for Module 5 Project 4 (Windows, Linux, macOS)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    repo_root = project_dir.parent
    workspace = project_dir / "workspace"

    bundled_source = project_dir / "fraud-detection-starter"
    sibling_source = repo_root / "fraud-detection-starter"
    if bundled_source.is_dir():
        source = bundled_source
    elif sibling_source.is_dir():
        source = sibling_source
    else:
        print(f"ERROR: fraud-detection-starter not found at {bundled_source} or {sibling_source}")
        return 1

    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(source, workspace)

    for sub in (".claude", "reports", "data"):
        (workspace / sub).mkdir(parents=True, exist_ok=True)

    shutil.copy2(script_dir / "settings_template.json", workspace / ".claude/settings.json")
    shutil.copy2(script_dir / "CLAUDE_md_template.md", workspace / "CLAUDE.md")

    resources = script_dir / "resources"
    if resources.is_dir():
        dest = workspace / "lab_resources"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(resources, dest)

    evidence = script_dir / "evidence"
    if evidence.is_dir():
        dest = workspace / "evidence"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(evidence, dest)

    diagrams = script_dir / "diagrams"
    if diagrams.is_dir():
        dest = workspace / "lab_resources" / "diagrams"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(diagrams, dest)

    print(f"Workspace ready: {workspace}")
    print("Seeded: CLAUDE.md, .claude/settings.json")
    print("Lab resources copied to: workspace/lab_resources/")
    print("Evidence placeholders: workspace/evidence/placeholders/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
