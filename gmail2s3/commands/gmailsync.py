import argparse
import datetime

from gmail2s3.commands.command_base import CommandBase
from gmail2s3.commands.utils import LoadVariables
from gmail2s3.gmailauth import (
    MessageQuery,
    Gmail2S3,
    WebHook,
)

from gmail2s3.config import GCONFIG


class GmailSyncCmd(CommandBase):
    name = "gmail-sync"
    help_message = "Sync emails to S3"

    def __init__(self, options):
        super().__init__(options)
        # self.conf_file = options.conf_file
        self.webhooks = [WebHook(**x) for x in options.webhooks["webhooks"]]
        self.message_query = MessageQuery(
            after=options.after,
            before=options.before,
            labels=options.labels,
            exclude_labels=options.exclude_labels,
        )
        self.conf = options.conf
        self._result = None
        self.info = options.info
        GCONFIG.load_conf(self.conf)

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument(
            "--conf",
            "-c",
            default={},
            required=False,
            action=LoadVariables,
            help="Path to configuration file of the application. Can set the GMAIL2S3_CONF_FILE envvar instead",
        )

        parser.add_argument(
            "--labels",
            "-l",
            required=False,
            action="append",
            default=[],
            help="label to match emails, repeat the option to match multiple labels: -l label1 -l label2",
        )

        parser.add_argument(
            "--exclude-labels",
            "-e",
            required=False,
            action="append",
            default=[],
            help="labels to exclude:  -e label1 -e label2",
        )

        parser.add_argument(
            "--before",
            "-b",
            required=False,
            type=datetime.datetime.fromisoformat,
            help="Match emails sent before [date]. ISO format: YYYY-MM-DD[THH:MM:SS]",
        )

        parser.add_argument(
            "--after",
            "-a",
            required=False,
            type=datetime.datetime.fromisoformat,
            help="Match emails sent after [date]. ISO format: YYYY-MM-DD[THH:MM:SS]",
        )

        parser.add_argument(
            "--info",
            "-i",
            required=False,
            default=False,
            action=argparse.BooleanOptionalAction,
            help="Returns only the number of emails matching the query",
        )

        parser.add_argument(
            "--webhooks",
            "-w",
            required=False,
            action=LoadVariables,
            default={"webhooks": []},
            help="""Define webhooks via a json, yaml file or inline: --webhook '{"webhooks": [{ \
            "endpoint": "https://toto.com/api/v1/uploaded",  \
            "params": {}, \
            "event": "upload_attachment", \
            "token": "private-token", \
            "headers": {"User-Agent": "gmail2s3-app"}, \
            "verify_ssl": true ]}'""",
        )

    def _call(self):
        gmailsyncer = Gmail2S3(message_query=self.message_query, webhooks=self.webhooks)
        if self.info:
            self._result = gmailsyncer.sync_emails_info()
        else:
            resp = gmailsyncer.sync_emails()
            self._result = {"total": len(resp), "synced_emails": resp}

    def _render_dict(self):
        return self._result

    def _render_console(self):
        return self._result
