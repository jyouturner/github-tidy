from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

@dataclass
class Config:
    protected_branches: List[str]
    inactivity_days: int
    retention_days: int
    github_token: str
    org_name: str
    slack_token: str
    slack_channel: str
    archive_prefix: str
    critical_tag_patterns: List[str]
    
    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()
        return cls(
            protected_branches=os.getenv('PROTECTED_BRANCHES', 'develop,stage,master').split(','),
            inactivity_days=int(os.getenv('INACTIVITY_DAYS', '30')),
            retention_days=int(os.getenv('RETENTION_DAYS', '60')),
            github_token=os.getenv('GITHUB_TOKEN', ''),
            org_name=os.getenv('GITHUB_ORG', ''),
            slack_token=os.getenv('SLACK_TOKEN', ''),
            slack_channel=os.getenv('SLACK_CHANNEL', '#github-notifications'),
            archive_prefix=os.getenv('ARCHIVE_PREFIX', 'archived/'),
            critical_tag_patterns=os.getenv('CRITICAL_TAG_PATTERNS', 'v*,release-*').split(',')
        ) 