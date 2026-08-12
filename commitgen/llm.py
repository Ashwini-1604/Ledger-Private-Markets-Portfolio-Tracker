"""Talks to the Anthropic API to turn a git diff into a commit message or
changelog entry. Isolated here so cli.py stays focused on UX."""

from dataclasses import dataclass
from typing import Optional

import anthropic

from .config import Config

STYLE_GUIDES = {
    "conventional": (
        "Use Conventional Commits format: `<type>(<scope>): <subject>`.\n"
        "Valid types: feat, fix, refactor, docs, test, chore, style, perf, build, ci.\n"
        "Scope is optional and should be the affected module/component, lowercase, no spaces."
    ),
    "gitmoji": (
        "Prefix the subject with a single relevant gitmoji (e.g. ✨ for new feature, "
        "🐛 for bug fix, ♻️ for refactor, 📝 for docs, ✅ for tests, 🔧 for config)."
    ),
    "plain": (
        "Write a plain, direct imperative-mood subject line with no prefix or tags "
        "(e.g. 'Add user authentication', not 'Added' or 'Adding')."
    ),
}


@dataclass
class CommitMessage:
    subject: str
    body: Optional[str] = None

    def full_text(self) -> str:
        if self.body:
            return f"{self.subject}\n\n{self.body}"
        return self.subject


def _client(cfg: Config) -> anthropic.Anthropic:
    if not cfg.api_key:
        raise RuntimeError(
            "No API key configured. Run `commitgen init` to set one up, "
            "or set the ANTHROPIC_API_KEY environment variable."
        )
    return anthropic.Anthropic(api_key=cfg.api_key)


def generate_commit_message(
    diff: str, stat_summary: str, cfg: Config, extra_instructions: str = ""
) -> CommitMessage:
    style_guide = STYLE_GUIDES.get(cfg.style, STYLE_GUIDES["conventional"])
    body_instruction = (
        "After the subject line, add a blank line then 2-4 bullet points explaining "
        "*what* changed and *why*, only if the diff is non-trivial. Skip the body for "
        "small, self-explanatory changes."
        if cfg.include_body
        else "Do not include a body — subject line only."
    )

    system_prompt = (
        "You are a senior engineer writing a git commit message for a diff you are "
        "about to commit. You write precise, honest commit messages grounded only in "
        "what the diff actually shows — never invent behavior, file names, or reasoning "
        "not evidenced in the diff.\n\n"
        f"Style rules:\n{style_guide}\n\n"
        f"Subject line must be {cfg.max_subject_length} characters or fewer, imperative "
        f"mood (\"Add\", \"Fix\", \"Remove\" — not \"Added\", \"Fixes\").\n"
        f"{body_instruction}\n\n"
        "Respond with ONLY the commit message text. No preamble, no markdown fences, "
        "no explanation of your choice."
    )

    user_prompt = (
        f"Changed files summary:\n{stat_summary}\n\n"
        f"Staged diff:\n```diff\n{diff}\n```\n"
    )
    if extra_instructions:
        user_prompt += f"\nAdditional context from the developer: {extra_instructions}\n"

    client = _client(cfg)
    response = client.messages.create(
        model=cfg.model,
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()

    if "\n\n" in text:
        subject, body = text.split("\n\n", 1)
        return CommitMessage(subject=subject.strip(), body=body.strip())
    return CommitMessage(subject=text.strip())


def generate_changelog(commit_log: str, cfg: Config, version_label: str = "Unreleased") -> str:
    system_prompt = (
        "You are a release manager writing a changelog entry from a list of raw git "
        "commit subject lines. Group related commits into clear categories: "
        "Added, Changed, Fixed, Removed (Keep a Changelog style). Omit empty categories. "
        "Merge duplicate/near-duplicate entries. Write for end users, not developers — "
        "describe user-facing impact, not implementation detail, when the commit message "
        "allows you to infer it. Never invent changes not implied by the commit list.\n\n"
        "Respond in Markdown only, starting with a `## {version}` heading. No preamble."
    )

    client = _client(cfg)
    response = client.messages.create(
        model=cfg.model,
        max_tokens=800,
        system=system_prompt.replace("{version}", version_label),
        messages=[{"role": "user", "content": f"Commit subjects:\n{commit_log}"}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
