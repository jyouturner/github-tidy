import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from github_branch_manager.branch_manager import BranchManager
from github_branch_manager.config import Config

@pytest.fixture
def config():
    return Config(
        protected_branches=['develop', 'stage', 'master'],
        inactivity_days=30,
        retention_days=60,
        github_token='dummy-token',
        org_name='test-org',
        slack_token='slack-token'
    )

@pytest.fixture
def branch_manager(config):
    with patch('github_branch_manager.branch_manager.Github'):
        return BranchManager(config)

def test_is_branch_inactive(branch_manager):
    mock_branch = Mock()
    mock_branch.commit.commit.author.date = datetime.now() - timedelta(days=31)
    assert branch_manager.is_branch_inactive(mock_branch) is True

def test_should_not_archive_protected_branch(branch_manager):
    mock_branch = Mock()
    mock_branch.name = 'develop'
    assert branch_manager.should_archive_branch(mock_branch) is False 