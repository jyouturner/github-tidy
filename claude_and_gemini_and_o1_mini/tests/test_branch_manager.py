import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from github_branch_manager.branch_manager import BranchManager
from github_branch_manager.config import Config
from github.Branch import Branch
from github.Commit import Commit
from github.GitCommit import GitCommit
from github.PullRequest import PullRequest
from github.Tag import Tag
from github.Repository import Repository
from github.GithubException import RateLimitExceededException
from github.GitRef import GitRef

@pytest.fixture
def config():
    """Fixture providing test configuration"""
    return Config(
        github_token="test_token",
        org_name="test_org",
        slack_token="test_slack_token",
        slack_channel="#test-channel",
        protected_branches=["main", "develop"],
        inactivity_days=30,
        retention_days=60,
        archive_prefix="archived/",
        critical_tag_patterns=["v*", "release-*"],
        allow_auto_purge_critical=False
    )

@pytest.fixture
def mock_branch():
    """Fixture providing a mock branch"""
    branch = MagicMock(spec=Branch)
    branch.name = "feature/test-branch"
    branch.commit.sha = "test_sha"
    branch.commit.commit.author.date = datetime.now(timezone.utc) - timedelta(days=40)
    return branch

@pytest.fixture
def mock_repo():
    """Fixture providing a mock repository"""
    repo = MagicMock(spec=Repository)
    repo.name = "test-repo"
    return repo

@pytest.fixture
def mock_pull_request(merged=False):
    mock_pull = MagicMock(spec=PullRequest)
    mock_pull.merged = merged
    return mock_pull

@pytest.fixture
def mock_tag(sha='test_sha', name='test_tag'):
    mock_tag = MagicMock(spec=Tag)
    mock_commit = MagicMock(spec=Commit)
    mock_commit.sha = sha
    mock_tag.commit = mock_commit
    mock_tag.name = name
    return mock_tag

@pytest.fixture
def mock_github(mock_repo, mock_branch, mock_pull_request, mock_tag):
    mock_github = MagicMock()
    mock_org = MagicMock()
    mock_org.get_repo.return_value = mock_repo
    mock_github.get_organization.return_value = mock_org
    mock_repo.get_branches.return_value = [mock_branch]
    mock_repo.get_pulls.return_value = [mock_pull_request]
    mock_repo.get_tags.return_value = [mock_tag]
    return mock_github

@pytest.fixture
def branch_manager(config):
    """Fixture providing a BranchManager instance"""
    with patch('github.Github'):
        manager = BranchManager(config)
        manager.github = MagicMock()
        manager.org = MagicMock()
        manager.notifier = MagicMock()
        return manager

class TestBranchManager:
    def test_is_branch_inactive(self, branch_manager, mock_branch):
        """Test branch inactivity check"""
        # Branch is 40 days old, inactivity threshold is 30 days
        assert branch_manager.is_branch_inactive(mock_branch) == True

        # Test active branch
        mock_branch.commit.commit.author.date = datetime.now(timezone.utc)
        assert branch_manager.is_branch_inactive(mock_branch) == False

    def test_is_branch_merged(self, branch_manager, mock_repo, mock_branch):
        """Test branch merge status check"""
        # Mock pull requests
        mock_pr = MagicMock(spec=PullRequest)
        mock_pr.merged = True
        mock_repo.get_pulls.return_value = [mock_pr]

        assert branch_manager.is_branch_merged(mock_repo, mock_branch) == True

        # Test unmerged branch
        mock_pr.merged = False
        assert branch_manager.is_branch_merged(mock_repo, mock_branch) == False

    def test_has_open_prs(self, branch_manager, mock_repo):
        """Test open pull requests check"""
        mock_pulls = MagicMock()
        mock_pulls.totalCount = 1
        mock_repo.get_pulls.return_value = mock_pulls

        assert branch_manager.has_open_prs(mock_repo, "test-branch") == True

        mock_pulls.totalCount = 0
        assert branch_manager.has_open_prs(mock_repo, "test-branch") == False

    def test_has_critical_tags(self, branch_manager, mock_repo, mock_branch):
        """Test critical tags check"""
        # Mock tags
        mock_tag = MagicMock()
        mock_tag.name = "v1.0.0"
        mock_tag.commit.sha = mock_branch.commit.sha
        mock_repo.get_tags.return_value = [mock_tag]

        assert branch_manager.has_critical_tags(mock_repo, mock_branch) == True

        # Test non-critical tag
        mock_tag.name = "non-critical"
        assert branch_manager.has_critical_tags(mock_repo, mock_branch) == False

    def test_should_archive_branch(self, branch_manager, mock_repo, mock_branch):
        """Test branch archival decision"""
        # Mock necessary methods
        branch_manager.is_branch_inactive = MagicMock(return_value=True)
        branch_manager.is_branch_merged = MagicMock(return_value=True)
        branch_manager.has_open_prs = MagicMock(return_value=False)
        branch_manager.has_critical_tags = MagicMock(return_value=False)

        assert branch_manager.should_archive_branch(mock_repo, mock_branch) == True

        # Test protected branch
        mock_branch.name = "main"
        assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False

    def test_should_purge_branch(self, branch_manager, mock_repo, mock_branch):
        """Test branch purge decision"""
        # Mock branch with critical tags
        branch_manager.has_critical_tags = MagicMock(return_value=True)
        assert branch_manager.should_purge_branch(mock_repo, mock_branch) == False

        # Test branch without critical tags
        branch_manager.has_critical_tags = MagicMock(return_value=False)
        assert branch_manager.should_purge_branch(mock_repo, mock_branch) == True

    @patch('time.sleep')  # Prevent actual sleeping in tests
    def test_handle_rate_limit(self, mock_sleep, branch_manager):
        """Test rate limit handling"""
        mock_rate_limit = MagicMock()
        mock_rate_limit.remaining = 0
        mock_rate_limit.reset = datetime.now(timezone.utc) + timedelta(minutes=5)
        branch_manager.github.get_rate_limit.return_value.core = mock_rate_limit

        branch_manager.handle_rate_limit()
        mock_sleep.assert_called_once()

    def test_archive_branch(self, branch_manager, mock_repo, mock_branch):
        """Test branch archival process"""
        branch_manager.archive_branch(mock_repo, mock_branch)

        # Verify tag creation
        mock_repo.create_git_tag_and_release.assert_called_once()
        
        # Verify branch rename
        mock_repo.create_git_ref.assert_called_once()
        mock_repo.get_git_ref.assert_called_once()
        
        # Verify notification
        branch_manager.notifier.notify_archive.assert_called_once()

    def test_archive_branch_rate_limit(self, branch_manager, mock_repo, mock_branch):
        """Test branch archival with rate limit exception"""
        mock_repo.create_git_tag_and_release.side_effect = [
            RateLimitExceededException(403, "API rate limit exceeded"),
            None  # Succeed on retry
        ]

        branch_manager.archive_branch(mock_repo, mock_branch)

        assert mock_repo.create_git_tag_and_release.call_count == 2
        branch_manager.notifier.notify_archive.assert_called_once()

    def test_purge_branch(self, branch_manager, mock_repo, mock_branch):
        branch_manager.purge_branch(mock_repo, mock_branch)
        mock_repo.get_git_ref.assert_called_once()
        branch_manager.notifier.notify_deletion.assert_called_once() 