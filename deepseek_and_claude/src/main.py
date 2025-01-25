import functions_framework
from .config import Config
from .github_client import GitHubClient
from .branch_manager import BranchManager
from .notifier import Notifier

@functions_framework.http
def archive_branches(request):
    """Weekly branch archival function"""
    config = Config.from_env()
    github = GitHubClient(config.GITHUB_TOKEN)
    manager = BranchManager(github, config)
    notifier = Notifier(config.SLACK_WEBHOOK_URL, config.EMAIL_RECIPIENTS)
    
    actions = manager.process_repos()
    notifier.notify_actions(actions)
    
    return 'OK', 200

@functions_framework.http
def purge_branches(request):
    """Monthly branch purging function"""
    config = Config.from_env()
    github = GitHubClient(config.GITHUB_TOKEN)
    manager = BranchManager(github, config)
    notifier = Notifier(config.SLACK_WEBHOOK_URL, config.EMAIL_RECIPIENTS)
    
    actions = manager.process_repos()
    notifier.notify_actions(actions)
    
    return 'OK', 200 