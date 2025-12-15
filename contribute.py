#!/usr/bin/env python
"""
Fast GitHub Activity Generator using git fast-import.

A performance-optimized fork of https://github.com/Shpota/github-activity-generator
Uses git fast-import for ~2-3x faster commit generation.
"""
import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import randint
from typing import Optional

# Simple README content for generated repositories
README_CONTENT = "# Contributions\n\nGenerated contribution history.\n"


@dataclass(frozen=True)
class Config:
    """Immutable configuration for commit generation."""
    no_weekends: bool
    max_commits: int
    frequency: int
    days_before: int
    days_after: int
    repository: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    force: bool
    append: bool


def main(args: list[str] | None = None) -> None:
    """Entry point."""
    config = parse_args(args if args is not None else sys.argv[1:])
    validate_config(config)
    
    curr_date = datetime.now()
    
    # Setup repository - either clone existing or create new
    if config.append and config.repository:
        directory = setup_append_mode(config.repository)
    else:
        directory = create_directory(config.repository, curr_date)
        os.chdir(directory)
        git("init", "-b", "main")
    
    # Use provided credentials or read from global git config
    name = config.user_name or git_config("user.name")
    email = config.user_email or git_config("user.email")
    
    if not name:
        sys.exit("Error: git user.name not configured. Use -un or run: git config --global user.name 'Your Name'")
    if not email:
        sys.exit("Error: git user.email not configured. Use -ue or run: git config --global user.email 'you@example.com'")
    
    if config.user_name:
        git("config", "user.name", config.user_name)
    if config.user_email:
        git("config", "user.email", config.user_email)
    
    # Generate commits via fast-import
    parent_commit = get_head_commit() if config.append else None
    stream = build_fast_import_stream(config, name, email, curr_date, parent_commit)
    
    if stream:
        git_with_input("fast-import", "--quiet", input_data=stream)
        git("checkout", "main")
    
    if config.repository:
        if not config.append:
            git("remote", "add", "origin", config.repository)
        git("branch", "-M", "main")
        push_to_remote(config.force, config.append)
    
    print("\n\x1b[32m✓ Repository generated successfully\x1b[0m")


def setup_append_mode(repository: str) -> str:
    """Clone existing repo for append mode."""
    name = repository.rstrip("/")
    if name.endswith(".git"):
        name = name[:-4]
    name = name.rsplit("/", 1)[-1]
    
    print(f"Cloning {repository}...")
    
    try:
        subprocess.run(
            ["git", "clone", repository, name],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8").strip() if e.stderr else "Unknown error"
        sys.exit(f"Clone failed: {stderr}")
    
    os.chdir(name)
    return name


def get_head_commit() -> Optional[str]:
    """Get current HEAD commit SHA, or None if no commits."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def build_fast_import_stream(
    config: Config, 
    name: str, 
    email: str, 
    curr_date: datetime,
    parent_commit: Optional[str] = None,
) -> str:
    """Build git fast-import stream for all commits."""
    parts: list[str] = []
    mark = 1
    parent: int | str | None = parent_commit
    count = 0
    
    tz_offset = time.strftime("%z")
    start = curr_date.replace(hour=20, minute=0) - timedelta(config.days_before)
    max_commits = max(1, min(config.max_commits, 20))
    
    for day_offset in range(config.days_before + config.days_after):
        day = start + timedelta(day_offset)
        
        if config.no_weekends and day.weekday() >= 5:
            continue
        if randint(0, 100) > config.frequency:
            continue
        
        commits_today = randint(1, max_commits)
        
        for minute_offset in range(commits_today):
            commit_time = day + timedelta(minutes=minute_offset)
            msg = f"Contribution: {commit_time:%Y-%m-%d %H:%M}"
            timestamp = int(commit_time.timestamp())
            
            content_bytes = README_CONTENT.encode("utf-8")
            parts.append(f"blob\nmark :{mark}\ndata {len(content_bytes)}\n{README_CONTENT}")
            blob_mark = mark
            mark += 1
            
            msg_bytes = msg.encode("utf-8")
            commit = [
                f"commit refs/heads/main",
                f"mark :{mark}",
                f"committer {name} <{email}> {timestamp} {tz_offset}",
                f"data {len(msg_bytes)}",
                msg,
            ]
            
            if parent is not None:
                if isinstance(parent, str):
                    commit.append(f"from {parent}")
                else:
                    commit.append(f"from :{parent}")
            
            commit.append(f"M 100644 :{blob_mark} README.md\n")
            parts.append("\n".join(commit))
            
            parent = mark
            mark += 1
            count += 1
    
    if count:
        print(f"Generating {count} commits...")
    return "\n".join(parts)


def git(*args: str) -> None:
    """Run git command, exit with message on failure."""
    try:
        subprocess.run(["git", *args], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8").strip() if e.stderr else "Unknown error"
        sys.exit(f"Git error: {stderr}")


def git_try(*args: str) -> bool:
    """Run git command, return True on success, False on failure."""
    result = subprocess.run(["git", *args], capture_output=True)
    return result.returncode == 0


def push_to_remote(force: bool, append: bool = False) -> None:
    """Push to remote with optional force and helpful error messages."""
    if force:
        git("push", "-u", "origin", "main", "--force")
        return
    
    if git_try("push", "-u", "origin", "main"):
        return
    
    print("\n\x1b[33m⚠ Push rejected - remote has existing history.\x1b[0m")
    if append:
        print("  Your --append added commits, but push still needs --force.")
        print("  Run: git push origin main --force")
    else:
        print("  Use --append to preserve existing files, or --force to overwrite:")
        print("  python contribute.py -r <repo> --append")
        print("  python contribute.py -r <repo> --force")
    sys.exit(1)


def git_config(key: str) -> str:
    """Read git config value, returns empty string if not set."""
    result = subprocess.run(
        ["git", "config", "--global", key],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_with_input(*args: str, input_data: str) -> None:
    """Run git command with stdin, exit with message on failure."""
    try:
        subprocess.run(
            ["git", *args],
            input=input_data.encode("utf-8"),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8").strip() if e.stderr else "Unknown error"
        sys.exit(f"Git error: {stderr}")


def create_directory(repository: Optional[str], curr_date: datetime) -> str:
    """Create and return working directory name."""
    if repository:
        name = repository.rstrip("/")
        if name.endswith(".git"):
            name = name[:-4]
        name = name.rsplit("/", 1)[-1]
    else:
        name = f"repository-{curr_date:%Y-%m-%d-%H-%M-%S}"
    
    if os.path.exists(name):
        sys.exit(f"Error: Directory '{name}' already exists. Remove it or use a different name.")
    os.mkdir(name)
    return name


def validate_config(config: Config) -> None:
    """Validate configuration, exit on error."""
    if config.days_before < 0:
        sys.exit("Error: days_before must not be negative")
    if config.days_after < 0:
        sys.exit("Error: days_after must not be negative")
    if not 0 <= config.frequency <= 100:
        sys.exit("Error: frequency must be between 0 and 100")
    if not 1 <= config.max_commits <= 20:
        sys.exit("Error: max_commits must be between 1 and 20")
    if config.append and not config.repository:
        sys.exit("Error: --append requires --repository")


def parse_args(args: list[str]) -> Config:
    """Parse CLI arguments into Config."""
    p = argparse.ArgumentParser(description="Generate GitHub contribution history")
    p.add_argument("-nw", "--no_weekends", action="store_true",
                   help="Skip weekends")
    p.add_argument("-mc", "--max_commits", type=int, default=10,
                   help="Max commits per day (1-20)")
    p.add_argument("-fr", "--frequency", type=int, default=80,
                   help="Percentage of days to commit (0-100)")
    p.add_argument("-r", "--repository", type=str,
                   help="Remote repository URL to push to")
    p.add_argument("-un", "--user_name", type=str,
                   help="Override git user.name")
    p.add_argument("-ue", "--user_email", type=str,
                   help="Override git user.email")
    p.add_argument("-db", "--days_before", type=int, default=365,
                   help="Days before today to start")
    p.add_argument("-da", "--days_after", type=int, default=0,
                   help="Days after today to end")
    p.add_argument("-f", "--force", action="store_true",
                   help="Force push (overwrites remote history)")
    p.add_argument("-a", "--append", action="store_true",
                   help="Append to existing repo (clones first, preserves files)")
    
    a = p.parse_args(args)
    return Config(
        no_weekends=a.no_weekends,
        max_commits=a.max_commits,
        frequency=a.frequency,
        days_before=a.days_before,
        days_after=a.days_after,
        repository=a.repository,
        user_name=a.user_name,
        user_email=a.user_email,
        force=a.force,
        append=a.append,
    )


if __name__ == "__main__":
    main()
