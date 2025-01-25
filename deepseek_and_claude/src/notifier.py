import requests
import logging
from typing import List, Tuple

class Notifier:
    def __init__(self, slack_webhook: str, email_recipients: List[str]):
        self.slack_webhook = slack_webhook
        self.email_recipients = email_recipients
        self.logger = logging.getLogger(__name__)
    
    def notify_actions(self, actions: List[Tuple[str, str, str]]):
        if not actions:
            return
            
        message = "Branch cleanup summary:\n"
        for repo, branch, action in actions:
            message += f"- {action.title()}: {repo}/{branch}\n"
            
        if self.slack_webhook:
            self._send_slack(message)
        if self.email_recipients:
            self._send_email(message)
    
    def _send_slack(self, message: str):
        try:
            requests.post(self.slack_webhook, json={"text": message})
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_email(self, message: str):
        # TODO: Implement email sending logic (e.g., using sendgrid)
        pass 