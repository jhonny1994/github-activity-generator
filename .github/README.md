# GitHub Activity Generator (Fast Fork)

[![build](https://github.com/jhonny1994/github-activity-generator/workflows/build/badge.svg)](https://github.com/jhonny1994/github-activity-generator/actions?query=workflow%3Abuild)

A **performance-optimized fork** of [Shpota/github-activity-generator](https://github.com/Shpota/github-activity-generator) that generates a beautiful GitHub Contributions Graph **2-3x faster** using git fast-import.

## ⚠ Disclaimer

This script is for educational purposes and demonstrating GitHub mechanics. It should not be used to misrepresent professional contributions or coding activity.

## What's New in This Fork

| Feature | Original | This Fork |
|---------|----------|-----------|
| **Speed** | ~60s for 1 year | ~20s for 1 year |
| **Force push** | ❌ | ✅ `--force` |
| **Append mode** | ❌ | ✅ `--append` |
| **Clean README** | Accumulated text | Simple description |

## What it looks like

### Before 😐
![Before](before.png)
### After 💪 🔥
![After](after.png)

## Quick Start

```bash
# Create an empty GitHub repository (DO NOT initialize it)
# Then run:
python contribute.py --repository=git@github.com:user/repo.git
```

## Usage Examples

### Basic (1 year of contributions)
```bash
python contribute.py -r git@github.com:user/repo.git
```

### Human-like pattern (weekdays only, moderate activity)
```bash
python contribute.py -r git@github.com:user/repo.git -nw -fr=70 -mc=5
```

### Fill 5 years of history
```bash
python contribute.py -r git@github.com:user/repo.git -db=1825 --force
```

### Add to existing repo (preserves files)
```bash
python contribute.py -r git@github.com:user/repo.git --append
```

## All Options

| Option | Description | Default |
|--------|-------------|---------|
| `-r, --repository` | Remote repository URL | None |
| `-nw, --no_weekends` | Skip weekends | False |
| `-mc, --max_commits` | Max commits per day (1-20) | 10 |
| `-fr, --frequency` | % of days to commit (0-100) | 80 |
| `-db, --days_before` | Days before today | 365 |
| `-da, --days_after` | Days after today | 0 |
| `-un, --user_name` | Override git user.name | Global config |
| `-ue, --user_email` | Override git user.email | Global config |
| `-f, --force` | Force push (overwrite remote) | False |
| `-a, --append` | Clone first, preserve files | False |

```bash
python contribute.py --help
```

## System Requirements

- Python 3.10+
- Git

## Troubleshooting

### Activity not showing?
1. Wait a few minutes for GitHub to reindex
2. Enable private contributions if using a private repo
3. Verify your email matches GitHub settings:
   ```bash
   git config --get user.email
   ```

### Push rejected?
Use `--force` to overwrite existing history:
```bash
python contribute.py -r git@github.com:user/repo.git --force
```

### Want to preserve existing files?
Use `--append` to clone first:
```bash
python contribute.py -r git@github.com:user/repo.git --append
```

## Credits

Original project by [Shpota](https://github.com/Shpota/github-activity-generator)

Performance optimization using git fast-import.
