# commitgen — AI-generated commit messages & changelogs

A CLI tool that reads your staged `git diff`, sends it to Claude, and produces a
Conventional-Commits-style commit message — or a full changelog entry from your
commit history between two tags. Installs as a real `commitgen` command, and can
wire itself into `git commit` as a hook so it runs automatically.

## Why this exists

Writing good commit messages is the kind of small, constant friction that AI-assisted
tooling is genuinely good at removing — the model can see exactly what changed
(the diff) and just needs to describe it accurately. This project is deliberately
scoped around that one job rather than being a general "AI coding assistant."

## Features

- `commitgen` — generates a message for staged changes, lets you accept / edit / regenerate / cancel before committing
- `commitgen --dry-run` — just print the message, don't commit
- `commitgen changelog --from v1.2.0 --to v1.3.0` — turns raw commit subjects into a grouped, human-readable changelog (Keep a Changelog style: Added / Changed / Fixed / Removed)
- `commitgen install-hook` — installs a `prepare-commit-msg` git hook so plain `git commit` (opens your editor) comes pre-filled with an AI draft you can still edit
- Three message styles: `conventional`, `gitmoji`, `plain`
- Diffs are truncated safely for very large changesets rather than failing outright
- Never blocks a commit if generation fails (hook mode fails silently and falls through to your editor)

## Install

```bash
git clone <this-repo>
cd ai-commit-gen
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .
```

This registers a `commitgen` command on your PATH (via the `pyproject.toml`
`[project.scripts]` entry point — no manual symlinking needed).

## Setup

```bash
commitgen init
```

Prompts for your Anthropic API key (get one at console.anthropic.com) and your
preferred commit style. Saved to `~/.commitgen/config.toml` with `chmod 600` —
never touches your project's git history or gets committed by accident.

Alternatively, skip `init` and just set an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
git add -A
commitgen
```

```
╭──────────────── Generated commit message ────────────────╮
│ feat(auth): add JWT-based login endpoint                 │
│                                                            │
│ - Add /auth/login route with password verification        │
│ - Issue signed JWT on success                              │
╰────────────────────────────────────────────────────────────╯
Use this? [y/e/r/n]:
  (y)es · (e)dit · (r)egenerate · (n)o, cancel
```

- `y` — commits immediately with the generated message
- `e` — opens your `$EDITOR` pre-filled with the message so you can tweak it
- `r` — asks if you want to steer the regeneration (e.g. "mention this fixes issue #42"), then tries again
- `n` — cancels; your staged changes are untouched

### Automatic mode (git hook)

```bash
commitgen install-hook
git commit          # no -m — your editor opens pre-filled with an AI draft
```

Remove it any time with `commitgen uninstall-hook`.

### Changelog generation

```bash
commitgen changelog --from v1.2.0 --to v1.3.0 -o CHANGELOG.md
```

Reads commit subjects between the two tags, groups them by type, and appends
a Markdown changelog entry to the given file (or prints to stdout without `-o`).

## Project structure

```
ai-commit-gen/
  pyproject.toml         packaging + `commitgen` console-script entry point
  commitgen/
    cli.py                Click-based CLI, all commands live here
    git_utils.py           subprocess wrappers around git (diff, log, tags, commit)
    llm.py                 Anthropic API calls + prompt design
    config.py               config file (~/.commitgen/config.toml) + env var loading
    hook.py                 installs/removes the prepare-commit-msg git hook
```

## Distribution ("deployment" for a CLI tool)

A CLI tool doesn't get "deployed" to a server — it gets **packaged and distributed**
so other people can install it. Options, roughly in order of effort:

**1. Share via GitHub (simplest, good enough for a resume project)**
```bash
pip install git+https://github.com/your-username/ai-commit-gen.git
```
Anyone with the URL can install it directly — no publishing step needed.

**2. Build a wheel and share the file**
```bash
pip install build
python -m build
# produces dist/commitgen-0.1.0-py3-none-any.whl
pip install dist/commitgen-0.1.0-py3-none-any.whl
```

**3. Publish to PyPI (makes it `pip install commitgen`-able for anyone)**
```bash
pip install build twine
python -m build
twine upload dist/*
```
Requires a free PyPI account and an API token. After this, `pip install commitgen`
works for anyone, anywhere — worth doing if you want a portfolio link that's a real
`pip install` command rather than a GitHub URL.

**4. Global install without a venv, via pipx (nice UX to mention)**
```bash
pipx install git+https://github.com/your-username/ai-commit-gen.git
```
`pipx` installs CLI tools into isolated environments automatically — the standard
way developers install command-line tools written in Python, and worth namedropping
in an interview as a sign you know the ecosystem beyond `pip install -e .`.

## Notes on cost and safety

- Every call is a single Claude API request per commit message — cheap, and you
  control the model via `COMMITGEN_MODEL` or the config file.
- The tool never sends anything except the staged diff and file-change stats —
  no full repo contents, no `.env` files (unless you've staged one, which you
  shouldn't).
- Diffs over ~12,000 characters are truncated with a note to the model, so huge
  changesets degrade gracefully instead of failing or costing a fortune.
