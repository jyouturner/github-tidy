from datetime import datetime, timezone
from typing import List, Optional
from github import Github
from github.Repository import Repository
from github.Branch import Branch
import logging

class GitHubClient:
    def __init__(self, token: str):
        self.github = Github(token)
        self.logger = logging.getLogger(__name__)
    
    def get_org_repos(self, org_name: str) -> List[Repository]:
        try:
            org = self.github.get_organization(org_name)
            return list(org.get_repos())
        except Exception as e:
            self.logger.error(f"Failed to get repos for org {org_name}: {e}")
            return []
    
    def get_branch_last_activity(self, repo: Repository, branch: Branch) -> datetime:
        try:
            return branch.commit.commit.author.date
        except Exception as e:
            self.logger.error(f"Failed to get last activity for branch {branch.name}: {e}")
            return datetime.now(timezone.utc)
    
    def is_branch_merged(self, repo: Repository, branch: Branch, 
                        protected_branches: List[str]) -> bool:
        try:
            for base in protected_branches:
                pulls = repo.get_pulls(state='closed', 
                                     base=base,
                                     head=branch.name)
                if any(pr.merged for pr in pulls):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to check merge status for {branch.name}: {e}")
            return False
    
    def has_open_prs(self, repo: Repository, branch_name: str) -> bool:
        try:
            pulls = repo.get_pulls(state='open', head=branch_name)
            return pulls.totalCount > 0
        except Exception as e:
            self.logger.error(f"Failed to check PRs for {branch_name}: {e}")
            return True
    
    def has_critical_tags(self, repo: Repository, branch: Branch, 
                         patterns: List[str]) -> bool:
        try:
            import fnmatch
            commit_sha = branch.commit.sha
            for tag in repo.get_tags():
                if tag.commit.sha != commit_sha:
                    continue
                if any(fnmatch.fnmatch(tag.name, p) for p in patterns):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to check tags for {branch.name}: {e}")
            return True

    def archive_branch(self, repo: Repository, branch: Branch, 
                      archive_prefix: str) -> bool:
        try:
            new_name = f"{archive_prefix}{branch.name}"
            repo.create_git_ref(
                ref=f"refs/heads/{new_name}",
                sha=branch.commit.sha
            )
            repo.get_git_ref(f"heads/{branch.name}").delete()
            return True
        except Exception as e:
            self.logger.error(f"Failed to archive branch {branch.name}: {e}")
            return False 