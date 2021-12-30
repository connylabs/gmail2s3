from gmail2s3.gmailauth import GmailAuth
from gmail2s3.commands.command_base import CommandBase


class GmailAuthCmd(CommandBase):
    name = "gmailAuth"
    help_message = "Generate gmailAuths schema"
    output_default = "yaml"

    def __init__(self, options):
        super().__init__(options)
        self.gmailauth = None

    @classmethod
    def _add_arguments(cls, parser):
        pass

    def _call(self):
        self.gmailauth = GmailAuth()

    def _render_dict(self):
        return self.gmailauth

    def _render_console(self):
        return self.gmailauth
