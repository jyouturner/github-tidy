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

@pytest.fixture
def mock_config():
    return Config(
        protected_branches=['develop', 'master'],
        inactivity_days=30,
        retention_days=60,
        github_token='test_token',
        org_name='test_org',
        slack_token='slack_token',
        slack_channel='#test_channel',
        archive_prefix='archived/',
        critical_tag_patterns=['v*', 'release-*']
    )

@pytest.fixture
def mock_branch(commit_date=None):
    mock_branch = MagicMock(spec=Branch)
    mock_commit = MagicMock(spec=Commit)
    mock_git_commit = MagicMock(spec=GitCommit)
    mock_git_commit.author.date = commit_date if commit_date else datetime.now(timezone.utc) - timedelta(days=40)
    mock_commit.commit = mock_git_commit
    mock_branch.commit = mock_commit
    mock_branch.name = 'test-branch'
    return mock_branch

@pytest.fixture
def mock_repo():
    mock_repo = MagicMock(spec=Repository)
    mock_repo.name = 'test-repo'
    return mock_repo

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
def branch_manager(mock_config, mock_github):
    manager = BranchManager(mock_config)
    manager.github = mock_github
    return manager

def test_is_branch_inactive(branch_manager, mock_branch):
    assert branch_manager.is_branch_inactive(mock_branch) == True
    mock_branch.commit.commit.author.date = datetime.now(timezone.utc) - timedelta(days=20)
    assert branch_manager.is_branch_inactive(mock_branch) == False

def test_is_branch_merged(branch_manager, mock_repo, mock_branch, mock_pull_request):
    mock_repo.get_pulls.return_value = []
    assert branch_manager.is_branch_merged(mock_repo, mock_branch) == False
    mock_pull_request.merged = True
    mock_repo.get_pulls.return_value = [mock_pull_request]
    assert branch_manager.is_branch_merged(mock_repo, mock_branch) == True
    branch_manager.config.protected_branches = ['main']
    assert branch_manager.is_branch_merged(mock_repo, mock_branch) == False

def test_has_open_prs(branch_manager, mock_repo):
    mock_repo.get_pulls.return_value = []
    assert branch_manager.has_open_prs(mock_repo, 'test-branch') == False
    mock_repo.get_pulls.return_value = [MagicMock()]
    assert branch_manager.has_open_prs(mock_repo, 'test-branch') == True

def test_has_critical_tags(branch_manager, mock_repo, mock_branch, mock_tag):
    assert branch_manager.has_critical_tags(mock_repo, mock_branch) == False
    mock_tag.name = 'v1.0.0'
    assert branch_manager.has_critical_tags(mock_repo, mock_branch) == True
    mock_tag.name = 'test_tag'
    mock_tag.commit.sha = 'other_sha'
    assert branch_manager.has_critical_tags(mock_repo, mock_branch) == False

def test_should_archive_branch(branch_manager, mock_repo, mock_branch):
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == True
    mock_branch.name = 'develop'
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False
    mock_branch.name = 'archived/test-branch'
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False
    mock_branch.name = 'test-branch'
    mock_branch.commit.commit.author.date = datetime.now(timezone.utc) - timedelta(days=20)
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False
    mock_branch.commit.commit.author.date = datetime.now(timezone.utc) - timedelta(days=40)
    mock_repo.get_pulls.return_value = [MagicMock(merged=False)]
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False
    mock_repo.get_pulls.return_value = [MagicMock(merged=True)]
    mock_repo.get_pulls.return_value = [MagicMock(state='open')]
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False
    mock_repo.get_pulls.return_value = []
    mock_repo.get_tags.return_value = [MagicMock(name='v1.0.0')]
    assert branch_manager.should_archive_branch(mock_repo, mock_branch) == False

def test_should_purge_branch(branch_manager, mock_branch):
    archive_date = datetime.now(timezone.utc) - timedelta(days=70)
    assert branch_manager.should_purge_branch(mock_branch, archive_date) == True
    archive_date = datetime.now(timezone.utc) - timedelta(days=50)
    assert branch_manager.should_purge_branch(mock_branch, archive_date) == False

def test_archive_branch(branch_manager, mock_repo, mock_branch):
    branch_manager.archive_branch(mock_repo, mock_branch)
    mock_repo.create_git_ref.assert_called_once()
    mock_repo.get_git_ref.assert_called_once()
    branch_manager.notifier.notify_archive.assert_called_once()

def test_purge_branch(branch_manager, mock_repo, mock_branch):
    branch_manager.purge_branch(mock_repo, mock_branch)
    mock_repo.get_git_ref.assert_called_once()
    branch_manager.notifier.notify_deletion.assert_called_once() 