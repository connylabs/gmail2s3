import logging
import argparse
import os

from gmail2s3.commands.runserver import RunServerCmd
from gmail2s3.commands.version import VersionCmd
from gmail2s3.commands.openapi import OpenapiCmd
from gmail2s3.commands.gmailauth import GmailAuthCmd
from gmail2s3.commands.gmailsync import GmailSyncCmd


def all_commands():
    return {
        VersionCmd.name: VersionCmd,
        RunServerCmd.name: RunServerCmd,
        OpenapiCmd.name: OpenapiCmd,
        GmailAuthCmd.name: GmailAuthCmd,
        GmailSyncCmd.name: GmailSyncCmd,
    }


def get_parser(commands, parser=None, subparsers=None, env=None):
    if parser is None:
        parser = argparse.ArgumentParser()

    if subparsers is None:
        subparsers = parser.add_subparsers(help="command help")

    for command_class in commands.values():
        command_class.add_parser(subparsers, env)

    return parser


def set_cmd_env(env):
    """Allow commands to Set environment variables after being called"""
    if env is not None:
        for key, value in env.items():
            os.environ[key] = value


def cli():
    logging.basicConfig(level=logging.INFO)
    try:
        parser = get_parser(all_commands())
        unknown = None
        args, unknown = parser.parse_known_args()
        if len(list(vars(args))) == 0:
            parser.print_help()
            return
        set_cmd_env(args.env)
        if args.parse_unknown:
            args.func(args, unknown)
        else:
            args = parser.parse_args()
            args.func(args)

    except (argparse.ArgumentTypeError, argparse.ArgumentError) as exc:
        if os.getenv("GMAIL2S3_DEBUG", "false") == "true":
            raise
        parser.error(exc.message)
