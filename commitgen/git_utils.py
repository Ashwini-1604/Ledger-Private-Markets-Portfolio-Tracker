"""Thin wrappers around git CLI commands. Keeps subprocess calls in one place
so the rest of the tool never shells out directly."""

import subprocess
from dataclasses import dataclass
from typing import List, Optional


class NotAGitRepoError(Exception):
    pass


class NoStagedChangesError(Exception):
    pass


def _run(args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("git is not installed or not on PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr.strip() or f"git {' '.join(args)} failed")


def is_git_repo() -> bool:
    try:
        _run(["rev-parse", "--is-inside-work-tree"])
        return True
    except RuntimeError:
        return False


def get_staged_diff(max_chars: int = 12000) -> str:
    """Returns the staged diff (git diff --cached). Truncates very large
    diffs so we don't blow past LLM context limits or run up cost — a
    truncated diff still gives the model enough signal for a good message,
    and we tell the model it's truncated so it doesn't hallucinate specifics
    about files it can't see."""
    if not is_git_repo():
        raise NotAGitRepoError("Not inside a git repository.")

    diff = _run(["diff", "--cached", "--unified=3"])
    if not diff:
        raise NoStagedChangesError(
            "No staged changes found. Stage files first with `git add`."
        )

    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n\n[... diff truncated for length ...]"
    return diff


def get_staged_file_stats() -> str:
    """Short stat summary (files changed, insertions/deletions) — cheap
    context to include alongside the diff."""
    return _run(["diff", "--cached", "--stat"])


def get_current_branch() -> str:
    return _run(["rev-parse", "--abbrev-ref", "HEAD"])


def commit(message: str) -> None:
    _run(["commit", "-m", message])


@dataclass
class TagRange:
    from_ref: str
    to_ref: str


def list_tags() -> List[str]:
    out = _run(["tag", "--sort=-creatordate"])
    return [t for t in out.splitlines() if t.strip()]


def get_commit_log(from_ref: Optional[str], to_ref: str = "HEAD") -> str:
    """Returns a compact log (subject lines only) between two refs, for
    changelog generation. If from_ref is None, uses the whole history."""
    rev_range = f"{from_ref}..{to_ref}" if from_ref else to_ref
    log = _run(["log", rev_range, "--pretty=format:%s", "--no-merges"])
    return log


def get_repo_root() -> str:
    return _run(["rev-parse", "--show-toplevel"])
