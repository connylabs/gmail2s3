from __future__ import absolute_import, division, print_function
import subprocess
import os.path
import base64
import json

import pytest

from gmail2s3.commands.cli import all_commands, get_parser


LOCAL_DIR = os.path.dirname(__file__)


@pytest.fixture()
def cli_parser():
    return get_parser(all_commands())
