import os
import pytest
from github_branch_manager.config import Config

def test_config_from_env_default():
    config = Config.from_env()
    assert config.protected_branches == ['develop', 'stage', 'master']
    assert config.inactivity_days == 30
    assert config.retention_days == 60
    assert config.github_token == ''
    assert config.org_name == ''
    assert config.slack_token == ''
    assert config.slack_channel == '#github-notifications'
    assert config.archive_prefix == 'archived/'
    assert config.critical_tag_patterns == ['v*', 'release-*']

def test_config_from_env_custom():
    os.environ['PROTECTED_BRANCHES'] = 'main,test'
    os.environ['INACTIVITY_DAYS'] = '15'
    os.environ['RETENTION_DAYS'] = '90'
    os.environ['GITHUB_TOKEN'] = 'test_token'
    os.environ['GITHUB_ORG'] = 'test_org'
    os.environ['SLACK_TOKEN'] = 'slack_token'
    os.environ['SLACK_CHANNEL'] = '#test_channel'
    os.environ['ARCHIVE_PREFIX'] = 'custom/'
    os.environ['CRITICAL_TAG_PATTERNS'] = 'hotfix-*,bugfix-*'

    config = Config.from_env()
    assert config.protected_branches == ['main', 'test']
    assert config.inactivity_days == 15
    assert config.retention_days == 90
    assert config.github_token == 'test_token'
    assert config.org_name == 'test_org'
    assert config.slack_token == 'slack_token'
    assert config.slack_channel == '#test_channel'
    assert config.archive_prefix == 'custom/'
    assert config.critical_tag_patterns == ['hotfix-*', 'bugfix-*']

    # Clean up environment variables
    del os.environ['PROTECTED_BRANCHES']
    del os.environ['INACTIVITY_DAYS']
    del os.environ['RETENTION_DAYS']
    del os.environ['GITHUB_TOKEN']
    del os.environ['GITHUB_ORG']
    del os.environ['SLACK_TOKEN']
    del os.environ['SLACK_CHANNEL']
    del os.environ['ARCHIVE_PREFIX']
    del os.environ['CRITICAL_TAG_PATTERNS']

class TestConfig:
    """Tests for the Config class"""

    def test_from_env_with_required_vars(self, monkeypatch):
        """Test config creation with required environment variables"""
        env_vars = {
            'GITHUB_TOKEN': 'test_github_token',
            'GITHUB_ORG': 'test_org',
            'SLACK_TOKEN': 'test_slack_token'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = Config.from_env()
        assert config.github_token == 'test_github_token'
        assert config.org_name == 'test_org'
        assert config.slack_token == 'test_slack_token'

    def test_from_env_with_missing_required_vars(self):
        """Test config creation fails with missing required variables"""
        with pytest.raises(EnvironmentError) as exc_info:
            Config.from_env()
        assert "Missing required environment variables" in str(exc_info.value)

    def test_from_env_with_invalid_numeric_values(self, monkeypatch):
        """Test config creation fails with invalid numeric values"""
        env_vars = {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_ORG': 'test_org',
            'SLACK_TOKEN': 'test_slack_token',
            'INACTIVITY_DAYS': '-1',  # Invalid negative value
            'RETENTION_DAYS': '0'     # Invalid zero value
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(ValueError) as exc_info:
            Config.from_env()
        assert "must be positive integers" in str(exc_info.value)

    def test_from_env_with_optional_vars(self, monkeypatch):
        """Test config creation with optional variables"""
        env_vars = {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_ORG': 'test_org',
            'SLACK_TOKEN': 'test_slack_token',
            'SLACK_CHANNEL': '#custom-channel',
            'PROTECTED_BRANCHES': 'main,develop,staging',
            'INACTIVITY_DAYS': '45',
            'RETENTION_DAYS': '90',
            'ARCHIVE_PREFIX': 'archived-',
            'CRITICAL_TAG_PATTERNS': 'v*,release-*,hotfix-*',
            'ALLOW_AUTO_PURGE_CRITICAL': 'true'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = Config.from_env()
        assert config.slack_channel == '#custom-channel'
        assert config.protected_branches == ['main', 'develop', 'staging']
        assert config.inactivity_days == 45
        assert config.retention_days == 90
        assert config.archive_prefix == 'archived-'
        assert config.critical_tag_patterns == ['v*', 'release-*', 'hotfix-*']
        assert config.allow_auto_purge_critical is True

    def test_from_env_default_values(self, monkeypatch):
        """Test config creation with default values"""
        # Set only required variables
        env_vars = {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_ORG': 'test_org',
            'SLACK_TOKEN': 'test_slack_token'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = Config.from_env()
        assert config.slack_channel == '#github-notifications'
        assert config.protected_branches == ['main', 'develop']
        assert config.inactivity_days == 30
        assert config.retention_days == 60
        assert config.archive_prefix == 'archived/'
        assert config.critical_tag_patterns == ['v*', 'release-*']
        assert config.allow_auto_purge_critical is False

    def test_auto_purge_critical_values(self, monkeypatch):
        """Test different values for ALLOW_AUTO_PURGE_CRITICAL"""
        env_vars = {
            'GITHUB_TOKEN': 'test_token',
            'GITHUB_ORG': 'test_org',
            'SLACK_TOKEN': 'test_slack_token'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Test truthy values
        for value in ['true', '1', 'yes', 'True', 'TRUE']:
            monkeypatch.setenv('ALLOW_AUTO_PURGE_CRITICAL', value)
            config = Config.from_env()
            assert config.allow_auto_purge_critical is True

        # Test falsy values
        for value in ['false', '0', 'no', 'False', 'FALSE', '', 'invalid']:
            monkeypatch.setenv('ALLOW_AUTO_PURGE_CRITICAL', value)
            config = Config.from_env()
            assert config.allow_auto_purge_critical is False 