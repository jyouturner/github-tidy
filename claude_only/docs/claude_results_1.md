Let's create the GitHub branch management project. I'll help set up the core structure and components.

```
github-branch-manager/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── github_branch_manager/
│       ├── __init__.py
│       ├── main.py
│       ├── branch_manager.py
│       ├── config.py
│       ├── notifier.py
│       └── logger.py
├── tests/
│   └── __init__.py
├── .gitignore
├── Dockerfile
├── README.md
├── pyproject.toml
└── cloud-run-job.yaml
```
This creates a complete project structure. Key components:

1. Core functionality in `branch_manager.py`
2. Configuration management in `config.py`
3. Docker and Cloud Run setup
4. Poetry dependency management

To get started:

1. Initialize project:
```bash
poetry install
```

2. Set environment variables:
```bash
export GITHUB_TOKEN='your-token'
export GITHUB_ORG='your-org'
export SLACK_TOKEN='your-slack-token'
```

3. Build and deploy:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/github-branch-manager
gcloud run jobs create github-branch-manager --execute-now
```

Would you like me to implement any specific component in more detail?