from unittest.mock import MagicMock, patch
import pytest
from github_branch_manager.notifier import SlackNotifier
from slack_sdk.errors import SlackApiError

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

class TestSlackNotifier:
    """Tests for the SlackNotifier class"""

    @pytest.fixture
    def notifier(self):
        """Fixture providing a SlackNotifier instance with mocked client"""
        with patch('slack_sdk.WebClient') as mock_client:
            notifier = SlackNotifier('test_token', '#test-channel')
            notifier.client = mock_client
            return notifier

    def test_notify_archive(self, notifier):
        """Test archive notification"""
        notifier.notify_archive('test-repo', 'feature/test', 'archived-feature-test-20240101')
        
        notifier.client.chat_postMessage.assert_called_once()
        args = notifier.client.chat_postMessage.call_args[1]
        assert args['channel'] == '#test-channel'
        assert 'test-repo' in args['text']
        assert 'feature/test' in args['text']
        assert 'archived-feature-test-20240101' in args['text']

    def test_notify_deletion(self, notifier):
        """Test deletion notification"""
        notifier.notify_deletion('test-repo', 'archived/feature/test')
        
        notifier.client.chat_postMessage.assert_called_once()
        args = notifier.client.chat_postMessage.call_args[1]
        assert args['channel'] == '#test-channel'
        assert 'test-repo' in args['text']
        assert 'archived/feature/test' in args['text']

    def test_rate_limit_handling(self, notifier):
        """Test handling of Slack rate limits"""
        # Mock rate limit error
        rate_limit_response = {'error': 'ratelimited'}
        rate_limit_headers = {'Retry-After': '30'}
        error = SlackApiError('Rate limited', rate_limit_response, rate_limit_headers)
        
        # Set up the mock to fail once then succeed
        notifier.client.chat_postMessage.side_effect = [
            error,
            None  # Success on retry
        ]

        with patch('time.sleep') as mock_sleep:
            notifier.notify_archive('test-repo', 'feature/test', 'archived-tag')
            
            # Verify sleep was called with correct duration
            mock_sleep.assert_called_once_with(30)
            # Verify two attempts were made
            assert notifier.client.chat_postMessage.call_count == 2

    def test_other_slack_errors(self, notifier):
        """Test handling of non-rate-limit Slack errors"""
        error = SlackApiError('Channel not found', {'error': 'channel_not_found'})
        notifier.client.chat_postMessage.side_effect = error

        # Should log error but not raise exception
        notifier.notify_archive('test-repo', 'feature/test', 'archived-tag')
        notifier.notify_deletion('test-repo', 'feature/test')

        # Verify attempts were made
        assert notifier.client.chat_postMessage.call_count == 2 