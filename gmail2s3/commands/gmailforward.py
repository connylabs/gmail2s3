import argparse
import datetime
from copy import deepcopy
from gmail2s3.commands.command_base import CommandBase
from gmail2s3.commands.utils import LoadVariables
from gmail2s3.gmailauth import (
    MessageQuery,
    Gmail2S3,
)

from gmail2s3.config import GCONFIG

# pylint: disable=too-many-instance-attributes
class GmailForwardCmd(CommandBase):
    name = "gmail-forward"
    help_message = "Forward emails to another email address"

    def __init__(self, options):
        super().__init__(options)
        # self.conf_file = options.conf_file
        self.webhooks = []
        print(options.filter_to)
        self.message_query = MessageQuery(
            after=options.after,
            before=options.before,
            labels=options.labels,
            sender=options.filter_sender,
            to=options.filter_to,
            exclude_labels=options.exclude_labels,
        )

        self.conf = options.conf
        GCONFIG.load_conf(self.conf)
        self.s3conf = deepcopy(GCONFIG.s3)
        self.info = options.info
        self.raw = options.raw
        self.to = options.to
        self.prefix = options.prefix
        self._result = None
        self.set_label = options.set_label

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument(
            "--to", required=True, type=str, help="Address to forward emails to"
        )

        parser.add_argument(
            "--prefix",
            required=True,
            type=str,
            help="Add a prefix to the original email subject",
        )

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
            "--filter-sender",
            required=False,
            action="append",
            default=[],
            help="list of emails to match the sender (from)",
        )

        parser.add_argument(
            "--filter-to",
            required=False,
            action="append",
            default=[],
            help="list of emails to match the recipient",
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
            "--set-label",
            required=False,
            type=str,
            help="Set a label on successfully forwarded emails",
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
            "--raw",
            "-r",
            required=False,
            default=False,
            action=argparse.BooleanOptionalAction,
            help="Forward the raw email, only change the 'To'",
        )

    def _call(self):
        gmailsyncer = Gmail2S3(
            message_query=self.message_query, webhooks=[], s3conf=self.s3conf
        )
        if self.info:
            self._result = gmailsyncer.sync_emails_info()
        else:
            if self.raw:
                resp = gmailsyncer.forward_raw_emails(
                    to=self.to, flag_label=self.set_label
                )
            else:
                resp = gmailsyncer.forward_emails(
                    to=self.to, forward_prefix=self.prefix, flag_label=self.set_label
                )
            self._result = {"total": len(resp), "forwarded_emails": resp}

    def _render_dict(self):
        return self._result

    def _render_console(self):
        return self._result
