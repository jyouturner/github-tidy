from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .logger import setup_logger

logger = setup_logger()

class SlackNotifier:
    def __init__(self, token: str, channel: str):
        self.client = WebClient(token=token)
        self.channel = channel

    def notify_archive(self, repo: str, branch: str) -> None:
        try:
            text = f":file_folder: Branch `{branch}` in repository `{repo}` has been archived"
            self.client.chat_postMessage(channel=self.channel, text=text)
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")

    def notify_deletion(self, repo: str, branch: str) -> None:
        try:
            text = f":wastebasket: Branch `{branch}` in repository `{repo}` has been deleted"
            self.client.chat_postMessage(channel=self.channel, text=text)
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {str(e)}") 