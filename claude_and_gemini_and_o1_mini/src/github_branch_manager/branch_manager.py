from datetime import datetime, timedelta, timezone
from typing import List, Optional
from github import Github
from github.Repository import Repository
from github.Branch import Branch
from .config import Config
from .logger import setup_logger
from .notifier import SlackNotifier
import time
from github.GithubException import RateLimitExceededException, GithubException

logger = setup_logger()

class BranchManager:
    """
    Manages GitHub branches by archiving inactive ones and purging them after a retention period.
    """

    def __init__(self, config: Config):
        """
        Initializes the BranchManager with the given configuration.
        
        Args:
            config (Config): Configuration settings.
        """
        self.config = config
        self.github = Github(config.github_token)
        self.org = self.github.get_organization(config.org_name)
        self.notifier = SlackNotifier(config.slack_token, config.slack_channel)

    def handle_rate_limit(self):
        """Handles GitHub API rate limits by sleeping until reset."""
        core_rate_limit = self.github.get_rate_limit().core
        remaining = core_rate_limit.remaining
        reset_timestamp = core_rate_limit.reset.timestamp()
        current_timestamp = time.time()
        sleep_time = reset_timestamp - current_timestamp + 5  # Adding buffer

        if remaining == 0:
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
            time.sleep(max(sleep_time, 0))

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

    def should_purge_branch(self, repo: Repository, branch: Branch) -> bool:
        """
        Determines if a branch should be purged based on retention period and critical tags.

        Args:
            repo (Repository): The GitHub repository.
            branch (Branch): The GitHub branch to evaluate.

        Returns:
            bool: True if the branch should be purged, False otherwise.
        """
        if self.has_critical_tags(repo, branch) and not self.config.allow_auto_purge_critical:
            logger.info(f"Branch {branch.name} has critical tags and requires manual approval.")
            return False

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)
        return branch.commit.commit.author.date < cutoff_date

    def archive_branch(self, repo: Repository, branch: Branch) -> None:
        """
        Archives a branch by creating a tag and renaming it with a prefix.

        Args:
            repo (Repository): The GitHub repository.
            branch (Branch): The GitHub branch to archive.
        """
        try:
            self.handle_rate_limit()

            # Create tag before archiving
            tag_name = f"archived-{branch.name}-{datetime.now().strftime('%Y%m%d')}"
            repo.create_git_tag_and_release(
                tag=tag_name,
                tag_message=f"Archived branch {branch.name} on {datetime.now().strftime('%Y-%m-%d')}",
                release_name=f"Archive {branch.name}",
                release_message=f"Branch `{branch.name}` has been archived.",
                object=branch.commit.sha,
                type="commit",
                draft=False,
                prerelease=False
            )
            logger.info(f"Created tag {tag_name} for branch {branch.name} in {repo.name}")

            # Archive the branch by renaming
            new_name = f"{self.config.archive_prefix}{branch.name}"
            repo.create_git_ref(
                ref=f"refs/heads/{new_name}",
                sha=branch.commit.sha
            )
            repo.get_git_ref(f"heads/{branch.name}").delete()
            self.notifier.notify_archive(repo.name, branch.name, tag_name)
            logger.info(f"Archived branch {branch.name} in {repo.name}")

        except RateLimitExceededException:
            logger.error("GitHub rate limit exceeded. Attempting to sleep and retry.")
            self.handle_rate_limit()
            self.archive_branch(repo, branch)  # Retry once after sleeping
        except GithubException as e:
            logger.error(f"GitHub exception occurred while archiving {branch.name}: {e}")
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
                    if self.should_purge_branch(repo, branch):
                        self.purge_branch(repo, branch)
                except Exception as e:
                    logger.error(f"Failed to process branch {branch.name} for purging: {str(e)}") 