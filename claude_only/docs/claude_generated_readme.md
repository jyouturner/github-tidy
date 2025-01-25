# GitHub Branch Manager

Automated tool for managing GitHub repository branches according to defined retention policies.

## Features

- Automatic archival of inactive branches (30+ days without commits)
- Branch deletion after retention period (60+ days in archived state)
- Slack notifications for branch operations
- Cloud Logging integration
- Protected branches exclusion
- Cloud Run job implementation

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Configure environment variables:
```bash
export GITHUB_TOKEN='your-token'
export GITHUB_ORG='your-org'
export SLACK_TOKEN='your-slack-token'
```

3. Deploy to Cloud Run:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/github-branch-manager
gcloud run jobs create github-branch-manager --execute-now
```

4. Schedule job:
```bash
gcloud scheduler jobs create http github-branch-manager-weekly \
    --schedule="0 0 * * 0" \
    --uri="YOUR_CLOUD_RUN_JOB_URL" \
    --http-method=POST
```

## Development

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black .
poetry run isort .
```