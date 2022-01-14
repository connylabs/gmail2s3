from gmail2s3.gmailauth import GmailClient
from gmail2s3.commands.command_base import CommandBase


class GmailAuthCmd(CommandBase):
    name = "gmail-login"
    help_message = "Start the login flow to generate the offline google API token"

    def __init__(self, options):
        super().__init__(options)
        self.secret_key = options.google_secret_key
        self.gmail_token = options.token_path
        self.gmailauth = None

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument(
            "--google-secret-key",
            "-k",
            required=True,
            type=str,
            help="Path to the google client_secret.json",
        )
        parser.add_argument(
            "--token-path",
            "-t",
            required=False,
            type=str,
            help="Path to the google client_secret.json",
        )

    def _call(self):
        self.gmailauth = GmailClient(self.secret_key, self.gmail_token)
        self.gmailauth.auth()

    def _render_dict(self):
        return self.gmailauth.gmail_token

    def _render_console(self):
        return self.gmailauth.gmail_token
