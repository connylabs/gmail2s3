from __future__ import absolute_import, division, print_function

import pytest
import requests
import requests_mock

import gmail2s3
from gmail2s3.client import DEFAULT_SERVER, Gmail2S3Client
from gmail2s3.commands.version import VersionCmd

DEFAULT_PREFIX = ""


def get_versioncmd(cli_parser, args=[]):
    options = cli_parser.parse_args(["version", DEFAULT_SERVER] + args)
    return VersionCmd(options)


def test_version_server_host(cli_parser):
    versioncmd = get_versioncmd(cli_parser)
    assert versioncmd.server_host == DEFAULT_SERVER


def test_version_init(cli_parser):
    versioncmd = get_versioncmd(cli_parser)
    assert versioncmd.api_version is None
    assert versioncmd.server_host == "http://localhost:8080"
    assert VersionCmd.name == "version"


def test_get_version(cli_parser, capsys):
    versioncmd = get_versioncmd(cli_parser)
    response = '{"gmail2s3-server": "0.23.0"}'
    with requests_mock.mock() as m:
        m.get(
            DEFAULT_SERVER + DEFAULT_PREFIX + "/version",
            complete_qs=True,
            text=response,
        )
        versioncmd.exec_cmd()
        out, err = capsys.readouterr()
        assert (
            out == "Api-version: {'gmail2s3-server': '0.23.0'}\nClient-version: %s\n"
            "" % gmail2s3.__version__
        )
        assert versioncmd._render_dict() == {
            "api-version": {"gmail2s3-server": "0.23.0"},
            "client-version": gmail2s3.__version__,
        }
        assert versioncmd.api_version == {"gmail2s3-server": "0.23.0"}


def test_get_version_api_error(cli_parser, capsys):
    versioncmd = get_versioncmd(cli_parser)
    response = '{"gmail2s3-server": "0.23.0"}'
    with requests_mock.mock() as m:
        m.get(
            DEFAULT_SERVER + DEFAULT_PREFIX + "/version",
            complete_qs=True,
            text=response,
            status_code=500,
        )
        versioncmd.exec_cmd()
        out, err = capsys.readouterr()
        assert (
            out == "Api-version: .. Connection error\nClient-version: %s\n"
            "" % gmail2s3.__version__
        )
        assert versioncmd._render_dict() == {
            "api-version": ".. Connection error",
            "client-version": gmail2s3.__version__,
        }
