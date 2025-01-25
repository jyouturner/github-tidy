from unittest.mock import MagicMock
import pytest
from github_branch_manager.notifier import SlackNotifier

@pytest.fixture
def mock_slack_client():
    return MagicMock()

@pytest.fixture
def slack_notifier(mock_slack_client):
    return SlackNotifier(token='test_token', channel='#test_channel')

def test_notify_archive(slack_notifier, mock_slack_client):
    slack_notifier.client = mock_slack_client
    slack_notifier.notify_archive(repo='test_repo', branch='test_branch')
    mock_slack_client.chat_postMessage.assert_called_once()

def test_notify_deletion(slack_notifier, mock_slack_client):
    slack_notifier.client = mock_slack_client
    slack_notifier.notify_deletion(repo='test_repo', branch='test_branch')
    mock_slack_client.chat_postMessage.assert_called_once() 