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