import os
import subprocess
from pathlib import Path


def _parse_version():
    # pylint: disable=no-member
    version_file = list(Path(__file__).resolve().parents[1].glob("VERSION"))
    # pylint: enable=no-member
    if version_file:
        return version_file[0].read_text().strip()
    return "0.0.1"


__version__ = _parse_version()


def get_git_sha():
    if os.path.exists("GIT_HEAD"):
        with open("GIT_HEAD", "r", encoding="utf-8") as openf:
            return openf.read()
    else:
        try:
            return (
                subprocess.check_output(["git", "rev-parse", "HEAD"])
                .strip()[0:8]
                .decode()
            )
        except (OSError, subprocess.CalledProcessError):
            pass
    return "unknown"
