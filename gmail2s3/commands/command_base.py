import argparse
import json
import sys
import subprocess
import requests

import yaml

from gmail2s3.client import Gmail2S3Client
from gmail2s3.commands.utils import ServerHost


class CommandBase:
    name = "command-base"
    help_message = "describe the command"
    server_client = Gmail2S3Client
    default_media_type = "-"
    parse_unknown = False
    output_default = "text"

    def __init__(self, args_options, unknown=None):
        self.unknown = unknown
        self.args_options = args_options
        self.output = args_options.output

    def render(self):
        if self.output == "none":
            return
        if self.output == "json":
            self._render_json()
        elif self.output == "yaml":
            self._render_yaml()
        else:
            print(self._render_console())

    def render_error(self, payload):
        if self.output == "json":
            self._render_json(payload)
        elif self.output == "yaml":
            self._render_yaml(payload)
        else:
            raise argparse.ArgumentTypeError(
                "\n"
                + yaml.safe_dump(payload, default_flow_style=False, width=float("inf"))
            )

    @classmethod
    def call(cls, options, unknown=None, render=True):
        # @TODO(ant31): all methods should have the 'unknown' parameter
        if cls.parse_unknown:
            obj = cls(options, unknown)
        else:
            obj = cls(options)
        obj.exec_cmd(render=render)

    def exec_cmd(self, render=True):
        try:
            self._call()
        except requests.exceptions.RequestException as exc:
            payload = {"message": str(exc)}
            if exc.response is not None:
                content = None
                try:
                    content = exc.response.json()
                except ValueError:
                    content = exc.response.content
                payload["response"] = content
            self.render_error(payload)
            sys.exit(2)
        except subprocess.CalledProcessError as exc:
            payload = {"message": str(exc.output)}
            self.render_error(payload)
            sys.exit(exc.returncode)

        if render:
            self.render()

    @classmethod
    def add_parser(cls, subparsers, env=None):
        parser = subparsers.add_parser(cls.name, help=cls.help_message)
        cls._add_output_option(parser)
        cls._add_arguments(parser)
        parser.set_defaults(
            func=cls.call, env=env, which_cmd=cls.name, parse_unknown=cls.parse_unknown
        )

    def _render_json(self, value=None):
        if not value:
            value = self._render_dict()
        print(json.dumps(value, indent=2, separators=(",", ": ")))

    def _render_dict(self):
        raise NotImplementedError

    def _render_console(self):
        raise NotImplementedError

    def _render_yaml(self, value=None):
        if not value:
            value = self._render_dict()
        print(yaml.safe_dump(value, default_flow_style=False, width=float("inf")))

    def _call(self):
        raise NotImplementedError

    @classmethod
    def _add_arguments(cls, parser):
        raise NotImplementedError

    @classmethod
    def _add_output_option(cls, parser):
        parser.add_argument(
            "--output",
            default=cls.output_default,
            choices=["text", "none", "json", "yaml"],
            help="output format",
        )

    @classmethod
    def _add_serverhost_arg(cls, parser):
        parser.add_argument(
            "server_host", nargs=1, action=ServerHost, help="server API url"
        )
        parser.add_argument(
            "-k",
            "--insecure",
            action="store_true",
            default=False,
            help="turn off verification of the https certificate",
        )
        parser.add_argument(
            "--cacert",
            nargs="?",
            default=None,
            help="CA certificate to verify peer against (SSL)",
        )

    @classmethod
    def _add_serverhost_option(cls, parser):
        parser.add_argument("-H", "--host", default=None, help=argparse.SUPPRESS)
        parser.add_argument(
            "-k",
            "--insecure",
            action="store_true",
            default=False,
            help="turn off verification of the https certificate",
        )
        parser.add_argument(
            "--cacert", default=None, help="CA certificate to verify peer against (SSL)"
        )
