from datetime import datetime, timedelta, timezone
from typing import List, Optional
from github import Github
from github.Repository import Repository
from github.Branch import Branch
from .config import Config
from .logger import setup_logger
from .notifier import SlackNotifier

logger = setup_logger()

class BranchManager:
    def __init__(self, config: Config):
        self.config = config
        self.github = Github(config.github_token)
        self.org = self.github.get_organization(config.org_name)
        self.notifier = SlackNotifier(config.slack_token, config.slack_channel)

    def is_branch_inactive(self, branch: Branch) -> bool:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.inactivity_days)
        last_commit = branch.commit.commit.author.date
        return last_commit < cutoff_date

    def is_branch_merged(self, repo: Repository, branch: Branch) -> bool:
        try:
            for base in self.config.protected_branches:
                pulls = repo.get_pulls(state='closed',
                                     base=base,
                                     head=branch.name)
                if any(pr.merged for pr in pulls):
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check merge status for {branch.name}: {e}")
            return False

    def has_open_prs(self, repo: Repository, branch_name: str) -> bool:
        try:
            pulls = repo.get_pulls(state='open', head=branch_name)
            return pulls.totalCount > 0
        except Exception as e:
            logger.error(f"Failed to check PRs for {branch_name}: {e}")
            return True

    def has_critical_tags(self, repo: Repository, branch: Branch) -> bool:
        try:
            import fnmatch
            commit_sha = branch.commit.sha
            for tag in repo.get_tags():
                if tag.commit.sha != commit_sha:
                    continue
                if any(fnmatch.fnmatch(tag.name, p) for p in self.config.critical_tag_patterns):
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check tags for {branch.name}: {e}")
            return True

    def should_archive_branch(self, repo: Repository, branch: Branch) -> bool:
        if branch.name in self.config.protected_branches:
            return False
        if branch.name.startswith(self.config.archive_prefix):
            return False
        if not self.is_branch_inactive(branch):
            return False
        if not self.is_branch_merged(repo, branch):
            return False
        if self.has_open_prs(repo, branch.name):
            return False
        if self.has_critical_tags(repo, branch):
            return False
        
        return True

    def should_purge_branch(self, branch: Branch, archive_date: datetime) -> bool:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
        return archive_date < cutoff_date

    def archive_branch(self, repo: Repository, branch: Branch) -> None:
        try:
            new_name = f"{self.config.archive_prefix}{branch.name}"
            repo.create_git_ref(
                ref=f"refs/heads/{new_name}",
                sha=branch.commit.sha
            )
            repo.get_git_ref(f"heads/{branch.name}").delete()
            self.notifier.notify_archive(repo.name, branch.name)
            logger.info(f"Archived branch {branch.name} in {repo.name}")
        except Exception as e:
            logger.error(f"Failed to archive {branch.name}: {str(e)}")
    
    def purge_branch(self, repo: Repository, branch: Branch) -> None:
        try:
            repo.get_git_ref(f"heads/{branch.name}").delete()
            self.notifier.notify_deletion(repo.name, branch.name)
            logger.info(f"Purged branch {branch.name} in {repo.name}")
        except Exception as e:
            logger.error(f"Failed to purge {branch.name}: {str(e)}")
            
    def process_branches(self, repo_name: str) -> None:
        repo = self.org.get_repo(repo_name)
        for branch in repo.get_branches():
            if self.should_archive_branch(repo, branch):
                self.archive_branch(repo, branch)

        for branch in repo.get_branches():
            if branch.name.startswith(self.config.archive_prefix):
                try:
                    commit_date = branch.commit.commit.author.date
                    if self.should_purge_branch(branch, commit_date):
                        self.purge_branch(repo, branch)
                except Exception as e:
                    logger.error(f"Failed to process branch {branch.name} for purging: {str(e)}") 