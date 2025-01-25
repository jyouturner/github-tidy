from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

@dataclass
class Config:
    """Configuration settings for the GitHub branch manager."""
    github_token: str
    org_name: str
    slack_token: str
    slack_channel: str
    protected_branches: List[str]
    inactivity_days: int
    retention_days: int
    archive_prefix: str
    critical_tag_patterns: List[str]
    allow_auto_purge_critical: bool

    @classmethod
    def from_env(cls) -> 'Config':
        """
        Creates a Config instance from environment variables.
        
        Raises:
            EnvironmentError: If required environment variables are missing.
            ValueError: If numeric values are invalid.
        """
        load_dotenv()
        
        # Check required variables
        required_vars = ['GITHUB_TOKEN', 'GITHUB_ORG', 'SLACK_TOKEN']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        # Validate numeric values
        try:
            inactivity_days = int(os.getenv('INACTIVITY_DAYS', '30'))
            retention_days = int(os.getenv('RETENTION_DAYS', '60'))
            if inactivity_days < 1 or retention_days < 1:
                raise ValueError("INACTIVITY_DAYS and RETENTION_DAYS must be positive integers")
        except ValueError as e:
            raise ValueError(f"Invalid numeric configuration: {str(e)}")

        return cls(
            github_token=os.getenv('GITHUB_TOKEN'),
            org_name=os.getenv('GITHUB_ORG'),
            slack_token=os.getenv('SLACK_TOKEN'),
            slack_channel=os.getenv('SLACK_CHANNEL', '#github-notifications'),
            protected_branches=[b.strip() for b in os.getenv('PROTECTED_BRANCHES', 'main,develop').split(',')],
            inactivity_days=inactivity_days,
            retention_days=retention_days,
            archive_prefix=os.getenv('ARCHIVE_PREFIX', 'archived/'),
            critical_tag_patterns=[p.strip() for p in os.getenv('CRITICAL_TAG_PATTERNS', 'v*,release-*').split(',')],
            allow_auto_purge_critical=os.getenv('ALLOW_AUTO_PURGE_CRITICAL', 'false').lower() in ('true', '1', 'yes')
        ) 