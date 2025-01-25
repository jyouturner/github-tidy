To address the project requirements, let's outline the implementation steps and provide a structured solution.

### Step-by-Step Implementation Plan

1. **Setup and Configuration:**
   - **Environment Setup:** Use Python 3.9+ and required libraries (`PyGithub`, `python-http-client` for Slack, `google-cloud-firestore`).
   - **GCP Configuration:**
     - Create a Google Cloud Project.
     - Enable Cloud Functions, Firestore, Secret Manager, and Cloud Scheduler.
   - **GitHub Token:**
     - Generate a GitHub Personal Access Token with `repo` scope.
     - Store the token in GCP Secret Manager.

2. **Firestore Database:**
   - Create a Firestore collection `branch_archival_log` to track archived branches with fields:
     - `repo` (string)
     - `original_branch` (string)
     - `archived_branch` (string)
     - `archival_date` (timestamp)
     - `purged` (boolean)

3. **Code Structure:**
   - **GitHub Client:** Handles interactions with GitHub API.
   - **Firestore Client:** Manages archival log entries.
   - **Notifier:** Sends Slack/Email notifications.
   - **Archiver/Purger:** Core logic for archival and purging processes.

### Solution Code

#### `github_client.py`

```python
from github import Github, Repository, Branch
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str):
        self.github = Github(token)
    
    def get_org_repos(self, org_name: str) -> list[Repository.Repository]:
        org = self.github.get_organization(org_name)
        return org.get_repos()
    
    def get_branches(self, repo: Repository.Repository, exclude_protected: list[str], exclude_prefix: str) -> list[Branch.Branch]:
        return [branch for branch in repo.get_branches() 
                if branch.name not in exclude_protected 
                and not branch.name.startswith(exclude_prefix)]
    
    def get_branch_last_commit_date(self, branch: Branch.Branch) -> datetime:
        return branch.commit.commit.author.date
    
    def is_merged_into_protected(self, repo: Repository.Repository, branch_name: str, protected_branches: list[str]) -> bool:
        for base in protected_branches:
            prs = repo.get_pulls(state='closed', base=base, head=branch_name)
            if any(pr.merged for pr in prs):
                return True
        return False
    
    def has_open_prs(self, repo: Repository.Repository, branch_name: str) -> bool:
        return repo.get_pulls(state='open', head=branch_name).totalCount > 0
    
    def has_critical_tags(self, repo: Repository.Repository, branch: Branch.Branch, patterns: list[str]) -> bool:
        from fnmatch import fnmatch
        commit_sha = branch.commit.sha
        tags = [tag.name for tag in repo.get_tags() if tag.commit.sha == commit_sha]
        return any(fnmatch(tag, pattern) for tag in tags for pattern in patterns)
    
    def create_archived_branch(self, repo: Repository.Repository, original_branch: str, sha: str) -> bool:
        archived_name = f"archived/{original_branch}"
        try:
            repo.create_git_ref(f"refs/heads/{archived_name}", sha)
            return True
        except Exception as e:
            logger.error(f"Failed to create archived branch: {e}")
            return False
    
    def delete_branch(self, repo: Repository.Repository, branch_name: str) -> bool:
        try:
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete branch: {e}")
            return False
    
    def create_tag(self, repo: Repository.Repository, sha: str, tag_name: str) -> bool:
        try:
            repo.create_git_tag(tag_name, "Archived branch", sha, "commit")
            repo.create_git_ref(f"refs/tags/{tag_name}", sha)
            return True
        except Exception as e:
            logger.error(f"Failed to create tag: {e}")
            return False
```

#### `firestore_client.py`

```python
from google.cloud import firestore
from datetime import datetime

class FirestoreClient:
    def __init__(self):
        self.db = firestore.Client()
        self.collection = "branch_archival_log"
    
    def log_archive(self, repo: str, original_branch: str, archived_branch: str):
        doc_ref = self.db.collection(self.collection).document()
        doc_ref.set({
            "repo": repo,
            "original_branch": original_branch,
            "archived_branch": archived_branch,
            "archival_date": datetime.now(),
            "purged": False
        })
    
    def get_entries_to_purge(self, cutoff: datetime) -> list:
        return self.db.collection(self.collection) \
            .where("archival_date", "<=", cutoff) \
            .where("purged", "==", False) \
            .stream()
    
    def mark_purged(self, doc_id: str):
        self.db.collection(self.collection).document(doc_id).update({"purged": True})
```

#### `notifier.py`

```python
import requests
import smtplib
from email.mime.text import MIMEText

class Notifier:
    def __init__(self, slack_webhook: str, email_sender: str, email_password: str):
        self.slack_webhook = slack_webhook
        self.email_sender = email_sender
        self.email_password = email_password
    
    def send_slack(self, message: str):
        if self.slack_webhook:
            requests.post(self.slack_webhook, json={"text": message})
    
    def send_email(self, to: str, subject: str, body: str):
        if self.email_sender and self.email_password:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = to
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, to, msg.as_string())
```

#### `archiver.py` (Cloud Function)

```python
import os
import logging
from datetime import datetime, timedelta
from github_client import GitHubClient
from firestore_client import FirestoreClient
from notifier import Notifier

logging.basicConfig(level=logging.INFO)

def archive_branches(request):
    # Config
    config = {
        "github_token": os.environ["GITHUB_TOKEN"],
        "github_org": os.environ["GITHUB_ORG"],
        "protected_branches": os.environ.get("PROTECTED_BRANCHES", "master,develop,stage").split(","),
        "critical_tag_patterns": os.environ.get("CRITICAL_TAG_PATTERNS", "v*,release-*").split(","),
        "inactivity_days": int(os.environ.get("INACTIVITY_DAYS", 30)),
        "slack_webhook": os.environ.get("SLACK_WEBHOOK"),
        "email_sender": os.environ.get("EMAIL_SENDER"),
        "email_password": os.environ.get("EMAIL_PASSWORD")
    }

    # Initialize clients
    github = GitHubClient(config["github_token"])
    firestore = FirestoreClient()
    notifier = Notifier(config["slack_webhook"], config["email_sender"], config["email_password"])

    # Process each repo
    for repo in github.get_org_repos(config["github_org"]):
        branches = github.get_branches(repo, config["protected_branches"], "archived/")
        for branch in branches:
            try:
                last_commit = github.get_branch_last_commit_date(branch)
                if (datetime.now() - last_commit).days < config["inactivity_days"]:
                    continue

                if not github.is_merged_into_protected(repo, branch.name, config["protected_branches"]):
                    continue

                if github.has_open_prs(repo, branch.name):
                    continue

                if github.has_critical_tags(repo, branch, config["critical_tag_patterns"]):
                    continue

                if github.create_archived_branch(repo, branch.name, branch.commit.sha):
                    if github.delete_branch(repo, branch.name):
                        firestore.log_archive(repo.name, branch.name, f"archived/{branch.name}")
                        notifier.send_slack(f"Archived {branch.name} in {repo.name}")
                        if config.get("CREATE_TAG"):
                            github.create_tag(repo, branch.commit.sha, f"archived-{branch.name}-{datetime.now().strftime('%Y%m%d')}")
            except Exception as e:
                logging.error(f"Error processing {repo.name}/{branch.name}: {e}")

    return "OK"
```

#### `purger.py` (Cloud Function)

```python
import os
import logging
from datetime import datetime, timedelta
from github_client import GitHubClient
from firestore_client import FirestoreClient
from notifier import Notifier

logging.basicConfig(level=logging.INFO)

def purge_branches(request):
    config = {
        "github_token": os.environ["GITHUB_TOKEN"],
        "retention_days": int(os.environ.get("RETENTION_DAYS", 60)),
        "slack_webhook": os.environ.get("SLACK_WEBHOOK"),
        "email_sender": os.environ.get("EMAIL_SENDER"),
        "email_password": os.environ.get("EMAIL_PASSWORD")
    }

    github = GitHubClient(config["github_token"])
    firestore = FirestoreClient()
    notifier = Notifier(config["slack_webhook"], config["email_sender"], config["email_password"])
    cutoff = datetime.now() - timedelta(days=config["retention_days"])

    for entry in firestore.get_entries_to_purge(cutoff):
        try:
            repo = github.github.get_repo(entry.to_dict()["repo"])
            archived_branch = entry.to_dict()["archived_branch"]

            if github.has_open_prs(repo, archived_branch):
                continue

            branch = repo.get_branch(archived_branch)
            if github.has_critical_tags(repo, branch, config.get("critical_tag_patterns", [])):
                continue

            if github.delete_branch(repo, archived_branch):
                firestore.mark_purged(entry.id)
                notifier.send_slack(f"Purged {archived_branch} in {repo.name}")
        except Exception as e:
            logging.error(f"Error purging {entry.id}: {e}")

    return "OK"
```

### Deployment Steps

1. **Deploy Cloud Functions:**
   - **Archiver Function:** Deploy with HTTP trigger, environment variables from Secret Manager.
   - **Purger Function:** Deploy similarly.

2. **Schedule with Cloud Scheduler:**
   - **Archiver:** Weekly trigger (e.g., every Monday 2 AM).
   - **Purger:** Monthly trigger (e.g., 1st day of the month 3 AM).

3. **Monitoring:**
   - Use Cloud Logging to monitor function executions.
   - Set up alerts for failures.

### Notes

- **Security:** Ensure all secrets (GitHub token, email credentials) are stored in Secret Manager and not hard-coded.
- **Testing:** Test extensively in a staging environment before production deployment.
- **Error Handling:** Enhance with retries for API calls and better error recovery.

This structured approach efficiently handles branch archival and purging while adhering to the defined policies and leveraging GCP services for scalability and reliability.