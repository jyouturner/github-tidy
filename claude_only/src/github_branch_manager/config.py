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
    
    @classmethod
    def from_env(cls) -> 'Config':
        load_dotenv()
        return cls(
            protected_branches=['develop', 'stage', 'master'],
            inactivity_days=30,
            retention_days=60,
            github_token=os.getenv('GITHUB_TOKEN', ''),
            org_name=os.getenv('GITHUB_ORG', ''),
            slack_token=os.getenv('SLACK_TOKEN', '')
        ) 