# Github Tidy by Claude and Gemini

A tool for automated GitHub branch management that archives inactive branches and purges old archived branches based on configurable policies.

## Features

- **Smart Branch Archival**
  - Archives inactive branches based on last commit date
  - Creates reference tags before archiving
  - Respects protected branches and open pull requests
  - Handles branches with critical tags separately

- **Configurable Purging**
  - Purges archived branches after retention period
  - Optional manual approval for branches with critical tags
  - Rate limit handling for GitHub API

- **Notifications & Logging**
  - Slack notifications for archival and deletion events
  - Comprehensive logging with Google Cloud Logging

- **Flexible Scheduling**
  - Separate modes for archival and purging operations
  - Can be scheduled independently via cron or other schedulers

## Requirements

- Python 3.8+
- GitHub access token with repo permissions
- Slack bot token (for notifications)
- Google Cloud project (for logging)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/github-tidy.git
cd github-tidy
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file with your configuration:
```env
# Required
GITHUB_TOKEN=your_github_token
GITHUB_ORG=your_organization
SLACK_TOKEN=your_slack_bot_token

# Optional with defaults
SLACK_CHANNEL=#github-notifications
PROTECTED_BRANCHES=main,develop
INACTIVITY_DAYS=30
RETENTION_DAYS=60
ARCHIVE_PREFIX=archived/
CRITICAL_TAG_PATTERNS=v*,release-*
ALLOW_AUTO_PURGE_CRITICAL=false
```

## Usage

The tool can be run in three modes:

### Archive Mode
Archives inactive branches that meet the criteria:
```bash
poetry run github-tidy --mode archive
```

### Purge Mode
Purges archived branches after retention period:
```bash
poetry run github-tidy --mode purge
```

### All Mode (Default)
Runs both archive and purge operations:
```bash
poetry run github-tidy --mode all
```

## Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | - | Yes |
| `GITHUB_ORG` | GitHub organization name | - | Yes |
| `SLACK_TOKEN` | Slack bot token for notifications | - | Yes |
| `SLACK_CHANNEL` | Slack channel for notifications | #github-notifications | No |
| `PROTECTED_BRANCHES` | Comma-separated list of protected branches | main,develop | No |
| `INACTIVITY_DAYS` | Days of inactivity before archival | 30 | No |
| `RETENTION_DAYS` | Days to retain archived branches | 60 | No |
| `ARCHIVE_PREFIX` | Prefix for archived branches | archived/ | No |
| `CRITICAL_TAG_PATTERNS` | Comma-separated glob patterns for critical tags | v*,release-* | No |
| `ALLOW_AUTO_PURGE_CRITICAL` | Allow auto-purging branches with critical tags | false | No |

## Branch Management Policy

### Archival Criteria
A branch will be archived if ALL of these conditions are met:
- Not a protected branch
- Inactive for specified period
- Has been merged to a protected branch
- No open pull requests
- No critical tags (unless configured otherwise)

### Purge Criteria
An archived branch will be purged if:
- Has been archived longer than retention period
- Does not have critical tags (or auto-purge is enabled)

## Scheduling

Example cron jobs for separate scheduling:

```bash
# Archive weekly (Monday 2 AM)
0 2 * * MON cd /path/to/github-tidy && poetry run github-tidy --mode archive

# Purge monthly (1st of month 3 AM)
0 3 1 * * cd /path/to/github-tidy && poetry run github-tidy --mode purge
```

## Error Handling

The tool includes robust error handling for:
- GitHub API rate limits (automatic retry)
- Missing configuration
- Invalid numeric values
- API failures
- Network issues

## Logging

All operations are logged to:
- Console output
- Google Cloud Logging (if configured)
- Slack notifications (for important events)

## Development

### Running Tests
```bash
poetry run pytest
```

### Type Checking
```bash
poetry run mypy src
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
