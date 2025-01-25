from dataclasses import dataclass
from typing import List
import os

@dataclass
class Config:
    GITHUB_TOKEN: str
    GITHUB_ORG: str
    PROTECTED_BRANCHES: List[str] = ("develop", "stage", "master")
    ARCHIVE_PREFIX: str = "archived/"
    INACTIVITY_DAYS: int = 30
    RETENTION_DAYS: int = 60
    CRITICAL_TAG_PATTERNS: List[str] = ("v*", "release-*")
    SLACK_WEBHOOK_URL: str = ""
    ENABLE_EMAIL: bool = False
    EMAIL_RECIPIENTS: List[str] = ()
    
    @classmethod
    def from_env(cls):
        return cls(
            GITHUB_TOKEN=os.getenv("GITHUB_TOKEN"),
            GITHUB_ORG=os.getenv("GITHUB_ORG"),
            PROTECTED_BRANCHES=os.getenv("PROTECTED_BRANCHES", "develop,stage,master").split(","),
            SLACK_WEBHOOK_URL=os.getenv("SLACK_WEBHOOK_URL", ""),
            EMAIL_RECIPIENTS=os.getenv("EMAIL_RECIPIENTS", "").split(",")
        ) 