from datetime import datetime, timezone, timedelta
from typing import List, Tuple
import logging
from google.cloud import firestore
from .github_client import GitHubClient
from .config import Config
from github.Repository import Repository
from github.Branch import Branch

class BranchManager:
    def __init__(self, github_client: GitHubClient, config: Config):
        self.github = github_client
        self.config = config
        self.db = firestore.Client()
        self.logger = logging.getLogger(__name__)
    
    def process_repos(self) -> List[Tuple[str, str, str]]:
        """Returns list of (repo_name, branch_name, action) tuples"""
        actions = []
        for repo in self.github.get_org_repos(self.config.GITHUB_ORG):
            actions.extend(self._process_repo(repo))
        return actions
    
    def _process_repo(self, repo: Repository) -> List[Tuple[str, str, str]]:
        actions = []
        for branch in repo.get_branches():
            if branch.name in self.config.PROTECTED_BRANCHES:
                continue
                
            if branch.name.startswith(self.config.ARCHIVE_PREFIX):
                if self._should_purge(repo, branch):
                    action = "purge"
                else:
                    continue
            else:
                if self._should_archive(repo, branch):
                    action = "archive"
                else:
                    continue
                    
            actions.append((repo.name, branch.name, action))
        return actions
    
    def _should_archive(self, repo: Repository, branch: Branch) -> bool:
        # Check inactivity
        last_activity = self.github.get_branch_last_activity(repo, branch)
        if (datetime.now(timezone.utc) - last_activity).days < self.config.INACTIVITY_DAYS:
            return False
            
        # Check merge status
        if not self.github.is_branch_merged(repo, branch, self.config.PROTECTED_BRANCHES):
            return False
            
        # Check open PRs
        if self.github.has_open_prs(repo, branch.name):
            return False
            
        # Check critical tags
        if self.github.has_critical_tags(repo, branch, self.config.CRITICAL_TAG_PATTERNS):
            return False
            
        return True
        
    def _should_purge(self, repo: Repository, branch: Branch) -> bool:
        doc_ref = self.db.collection('archived_branches').document(
            f"{repo.name}-{branch.name}"
        )
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
            
        archive_date = doc.get('archive_date')
        if (datetime.now(timezone.utc) - archive_date).days < self.config.RETENTION_DAYS:
            return False
            
        return True 