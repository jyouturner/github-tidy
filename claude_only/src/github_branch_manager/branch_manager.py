from datetime import datetime, timedelta
from typing import List, Optional
from github import Github
from .config import Config
from .logger import setup_logger
from .notifier import SlackNotifier

logger = setup_logger()

class BranchManager:
    def __init__(self, config: Config):
        self.config = config
        self.github = Github(config.github_token)
        self.org = self.github.get_organization(config.org_name)
        self.notifier = SlackNotifier(config.slack_token)

    def is_branch_inactive(self, branch) -> bool:
        cutoff_date = datetime.now() - timedelta(days=self.config.inactivity_days)
        last_commit = branch.commit.commit.author.date
        return last_commit < cutoff_date

    def should_archive_branch(self, branch) -> bool:
        if branch.name in self.config.protected_branches:
            return False
        if branch.name.startswith('archived/'):
            return False
        return self.is_branch_inactive(branch)

    def archive_branches(self, repo_name: str) -> None:
        repo = self.org.get_repo(repo_name)
        for branch in repo.get_branches():
            if self.should_archive_branch(branch):
                try:
                    new_name = f"archived/{branch.name}"
                    repo.get_git_ref(f"heads/{branch.name}").edit(
                        sha=branch.commit.sha,
                        force=True
                    )
                    self.notifier.notify_archive(repo_name, branch.name)
                    logger.info(f"Archived branch {branch.name} in {repo_name}")
                except Exception as e:
                    logger.error(f"Failed to archive {branch.name}: {str(e)}") 