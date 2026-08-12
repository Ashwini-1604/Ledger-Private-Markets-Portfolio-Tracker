"""commitgen — AI-assisted commit messages and changelogs.

Commands:
  commitgen init             interactive setup (API key + style)
  commitgen                  generate a message for staged changes, commit interactively
  commitgen --dry-run        just print the generated message, don't commit
  commitgen changelog        generate a changelog between two git tags (or full history)
  commitgen install-hook     wire commitgen into `git commit` automatically
  commitgen uninstall-hook   remove the hook
  commitgen hook-fill FILE   internal: called by the git hook, not for direct use
"""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text

from . import git_utils, hook
from .config import load_config, write_default_config, VALID_STYLES
from .llm import generate_commit_message, generate_changelog

console = Console()


@click.group(invoke_without_command=True)
@click.option("--dry-run", is_flag=True, help="Print the generated message without committing.")
@click.option("--instructions", "-m", default="", help="Extra context to steer the generated message.")
@click.pass_context
def cli(ctx, dry_run, instructions):
    if ctx.invoked_subcommand is None:
        ctx.invoke(generate, dry_run=dry_run, instructions=instructions)


@cli.command()
def init():
    """Interactive first-time setup: stores your API key and preferred style."""
    console.print(Panel.fit("commitgen setup", style="bold cyan"))
    api_key = Prompt.ask("Paste your Anthropic API key (from console.anthropic.com)", password=True)
    console.print(f"Available styles: {', '.join(VALID_STYLES)}")
    style = Prompt.ask("Commit message style", choices=list(VALID_STYLES), default="conventional")
    write_default_config(api_key, style)
    console.print("[green]Saved to ~/.commitgen/config.toml[/green]")
    console.print("Run [bold]commitgen[/bold] inside any git repo with staged changes to try it.")


@cli.command(name="generate", hidden=True)
@click.option("--dry-run", is_flag=True)
@click.option("--instructions", "-m", default="")
def generate(dry_run, instructions):
    """Generate a commit message for staged changes (default command)."""
    cfg = load_config()

    try:
        diff = git_utils.get_staged_diff()
        stats = git_utils.get_staged_file_stats()
    except git_utils.NotAGitRepoError:
        console.print("[red]Not inside a git repository.[/red]")
        sys.exit(1)
    except git_utils.NoStagedChangesError:
        console.print("[yellow]No staged changes.[/yellow] Stage files first with `git add`.")
        sys.exit(1)

    if not cfg.api_key:
        console.print("[red]No API key configured.[/red] Run [bold]commitgen init[/bold] first.")
        sys.exit(1)

    while True:
        with console.status("[cyan]Generating commit message…"):
            try:
                msg = generate_commit_message(diff, stats, cfg, instructions)
            except Exception as e:
                console.print(f"[red]Generation failed:[/red] {e}")
                sys.exit(1)

        console.print()
        console.print(Panel(Text(msg.full_text()), title="Generated commit message", border_style="cyan"))

        if dry_run:
            return

        choice = Prompt.ask(
            "[bold]Use this? [/bold]",
            choices=["y", "e", "r", "n"],
            default="y",
            show_choices=False,
        )
        console.print("  [dim](y)es · (e)dit · (r)egenerate · (n)o, cancel[/dim]")

        if choice == "y":
            git_utils.commit(msg.full_text())
            console.print("[green]Committed.[/green]")
            return
        elif choice == "e":
            edited = click.edit(msg.full_text())
            if edited and edited.strip():
                git_utils.commit(edited.strip())
                console.print("[green]Committed with your edits.[/green]")
            else:
                console.print("[yellow]Empty message, aborted.[/yellow]")
            return
        elif choice == "r":
            extra = Prompt.ask("Anything to steer the regeneration? (optional, Enter to skip)", default="")
            instructions = extra or instructions
            continue
        else:
            console.print("Cancelled. Your changes are still staged.")
            return


@cli.command()
@click.option("--from", "from_tag", default=None, help="Starting tag (defaults to the previous tag).")
@click.option("--to", "to_tag", default="HEAD", help="Ending ref (defaults to HEAD).")
@click.option("--version-label", default=None, help="Label for the changelog heading.")
@click.option("--output", "-o", default=None, help="Write to a file instead of stdout.")
def changelog(from_tag, to_tag, version_label, output):
    """Generate a changelog entry from commit history between two refs."""
    cfg = load_config()
    if not cfg.api_key:
        console.print("[red]No API key configured.[/red] Run [bold]commitgen init[/bold] first.")
        sys.exit(1)

    if from_tag is None:
        tags = git_utils.list_tags()
        from_tag = tags[0] if tags else None
        if from_tag:
            console.print(f"[dim]No --from given, using most recent tag: {from_tag}[/dim]")
        else:
            console.print("[dim]No tags found, using full commit history.[/dim]")

    log = git_utils.get_commit_log(from_tag, to_tag)
    if not log:
        console.print("[yellow]No commits found in that range.[/yellow]")
        sys.exit(1)

    label = version_label or (to_tag if to_tag != "HEAD" else "Unreleased")

    with console.status("[cyan]Writing changelog…"):
        entry = generate_changelog(log, cfg, version_label=label)

    if output:
        with open(output, "a") as f:
            f.write(entry + "\n\n")
        console.print(f"[green]Appended to {output}[/green]")
    else:
        console.print()
        console.print(Panel(entry, title=f"Changelog: {label}", border_style="cyan"))


@cli.command(name="install-hook")
def install_hook_cmd():
    """Install commitgen as a git prepare-commit-msg hook for this repo."""
    try:
        path = hook.install_hook()
        console.print(f"[green]Hook installed:[/green] {path}")
        console.print("Now `git commit` (without -m) will pre-fill an AI-generated message.")
    except Exception as e:
        console.print(f"[red]Could not install hook:[/red] {e}")
        sys.exit(1)


@cli.command(name="uninstall-hook")
def uninstall_hook_cmd():
    """Remove the commitgen git hook from this repo."""
    if hook.uninstall_hook():
        console.print("[green]Hook removed.[/green]")
    else:
        console.print("[yellow]No commitgen hook found.[/yellow]")


@cli.command(name="hook-fill", hidden=True)
@click.argument("commit_msg_file")
def hook_fill(commit_msg_file):
    """Called internally by the installed git hook. Writes a generated
    message into the commit message file git provides."""
    cfg = load_config()
    if not cfg.api_key:
        return  # silently skip if not configured; don't block the commit

    try:
        diff = git_utils.get_staged_diff()
        stats = git_utils.get_staged_file_stats()
        msg = generate_commit_message(diff, stats, cfg)
    except Exception:
        return  # never block a commit because generation failed

    with open(commit_msg_file, "r") as f:
        existing = f.read()

    with open(commit_msg_file, "w") as f:
        f.write(msg.full_text() + "\n\n" + existing)


def main():
    cli()


if __name__ == "__main__":
    main()
