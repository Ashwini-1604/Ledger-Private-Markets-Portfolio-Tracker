"""Installs commitgen as a `prepare-commit-msg` git hook, so `git commit`
(with no -m) automatically pre-fills the message with an AI-generated draft
that you can still edit in your editor before saving."""

import os
import stat
from pathlib import Path

from .git_utils import get_repo_root

HOOK_NAME = "prepare-commit-msg"

HOOK_SCRIPT = """#!/bin/sh
# Installed by commitgen (https://github.com/your-username/ai-commit-gen)
# Pre-fills the commit message with an AI-generated draft.
# Skips itself for merges, squashes, and amends (source != empty).

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

if [ -n "$COMMIT_SOURCE" ]; then
  exit 0
fi

commitgen hook-fill "$COMMIT_MSG_FILE" || exit 0
"""


def install_hook() -> str:
    repo_root = Path(get_repo_root())
    hooks_dir = repo_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / HOOK_NAME

    if hook_path.exists():
        existing = hook_path.read_text()
        if "commitgen" not in existing:
            backup = hook_path.with_suffix(".bak")
            hook_path.rename(backup)

    hook_path.write_text(HOOK_SCRIPT)
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(hook_path)


def uninstall_hook() -> bool:
    repo_root = Path(get_repo_root())
    hook_path = repo_root / ".git" / "hooks" / HOOK_NAME
    if hook_path.exists() and "commitgen" in hook_path.read_text():
        hook_path.unlink()
        backup = hook_path.with_suffix(".bak")
        if backup.exists():
            backup.rename(hook_path)
        return True
    return False
