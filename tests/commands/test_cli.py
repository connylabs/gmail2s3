import pytest
from pytest import raises

from gmail2s3.commands.cli import all_commands, cli, get_parser


# Real-test are in test_integration
def test_get_parser():
    parser = get_parser(all_commands())
    assert parser is not None


def test_cli_help(monkeypatch, capsys, cli_parser):
    monkeypatch.setattr("sys.argv", ["py.test", "--help"])
    with raises(SystemExit) as exc:
        cli()
    out, err = capsys.readouterr()
    cli_parser.print_help()
    out_help, err_help = capsys.readouterr()
    assert exc.value.code == 0
    assert out == out_help


def test_cli_bad_cmd(monkeypatch, capsys, cli_parser):
    monkeypatch.setattr("sys.argv", ["gmail2s3", "blabla"])
    with raises(SystemExit) as exc:
        cli()
    assert exc.value.code == 2
