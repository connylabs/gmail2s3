"""
Acquire runtime configuration from environment variables (etc).
"""

import os
import yaml


def logfile_path(jsonfmt=False, debug=False):
    """
    Returns the a logfileconf path following this rules:
      - conf/logging_debug_json.conf # jsonfmt=true,  debug=true
      - conf/logging_json.conf       # jsonfmt=true,  debug=false
      - conf/logging_debug.conf      # jsonfmt=false, debug=true
      - conf/logging.conf            # jsonfmt=false, debug=false
    Can be parametrized via envvars: JSONLOG=true, DEBUGLOG=true
    """
    _json = ""
    _debug = ""

    if jsonfmt or os.getenv("JSONLOG", "false").lower() == "true":
        _json = "_json"

    if debug or os.getenv("DEBUGLOG", "false").lower() == "true":
        _debug = "_debug"

    return os.path.join(GMAIL2S3_CONF_DIR, f"logging{_debug}{_json}.conf")


def getenv(name, default=None, convert=str):
    """
    Fetch variables from environment and convert to given type.

    Python's `os.getenv` returns string and requires string default.
    This allows for varying types to be interpolated from the environment.
    """

    # because os.getenv requires string default.
    internal_default = "$(none)$"
    val = os.getenv(name, internal_default)

    if val == internal_default:
        return default

    if callable(convert):
        return convert(val)

    return val


def envbool(value: str):
    return value and (value.lower() in ("1", "true", "True", "yes"))


APP_ENVIRON = getenv("APP_ENV", "development")

GMAIL2S3_API = getenv("GMAIL2S3_API", "https://gmail2s3.conny.dev")
GMAIL2S3_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
GMAIL2S3_ROOT_DIR = os.path.abspath(os.path.join(GMAIL2S3_SOURCE_DIR, "../"))
GMAIL2S3_CONF_DIR = os.getenv(
    "GMAIL2S3_CONF_DIR", os.path.join(GMAIL2S3_ROOT_DIR, "conf/")
)
GMAIL2S3_CONF_FILE = os.getenv("GMAIL2S3_CONF_FILE", None)
GMAIL2S3_DOWNLOAD_DIR = os.getenv("GMAIL2S3_DOWNLOAD_DIR", "/tmp/gmail2s3")
GMAIL2S3_TOKEN = os.getenv(
    "GMAIL2S3_TOKEN", "changeme"
)  # Set to None or empty to skip the token

GMAIL2S3_TMP_DIR = os.getenv("GMAIL2S3_TMP_DIR", "/tmp/gmail2s3")
GMAIL2S3_SENTRY_URL = os.getenv("GMAIL2S3_SENTRY_URL", None)
GMAIL2S3_SENTRY_ENV = os.getenv("GMAIL2S3_SENTRY_ENV", "development")
GMAIL2S3_DEBUG = getenv("GMAIL2S3_DEBUG", False, envbool)

GMAIL2S3_S3_ENDPOINT = os.getenv("GMAIL2S3_S3_ENDPOINT", None)
GMAIL2S3_S3_ACCESS_KEY = os.getenv("GMAIL2S3_S3_ACCESS_KEY", None)
GMAIL2S3_S3_SECRET_KEY = os.getenv("GMAIL2S3_S3_SECRET_KEY", None)
GMAIL2S3_S3_REGION = os.getenv("GMAIL2S3_S3_REGION", None)
GMAIL2S3_S3_PREFIX = os.getenv("GMAIL2S3_S3_PREFIX", None)
GMAIL2S3_S3_BUCKET = os.getenv("GMAIL2S3_S3_BUCKET", None)

PROMETHEUS_MULTIPROC_DIR = os.getenv(
    "PROMETHEUS_MULTIPROC_DIR", os.path.join(GMAIL2S3_TMP_DIR, "prometheus")
)
os.environ["PROMETHEUS_MULTIPROC_DIR"] = PROMETHEUS_MULTIPROC_DIR


class Gmail2S3Config:
    """
    Class to initialize the projects settings
    """

    def __init__(self, defaults=None, confpath=None):
        self.settings = {
            "gmail2s3": {
                "debug": GMAIL2S3_DEBUG,
                "env": APP_ENVIRON,
                "url": GMAIL2S3_API,
                "download_dir": GMAIL2S3_DOWNLOAD_DIR,
                "token": GMAIL2S3_TOKEN,
                "tmp_dir": GMAIL2S3_TMP_DIR,
                "prometheus_dir": PROMETHEUS_MULTIPROC_DIR,
            },
            "s3": {
                "endpoint": GMAIL2S3_S3_ENDPOINT,
                "access_key": GMAIL2S3_S3_ACCESS_KEY,
                "secret_key": GMAIL2S3_S3_SECRET_KEY,
                "region": GMAIL2S3_S3_REGION,
                "prefix": GMAIL2S3_S3_PREFIX,
                "bucket": GMAIL2S3_S3_BUCKET,
            },
            "gmail": {
                "client_secret": None,
                "gmail_token": None,
                "in_labels": [],
                "out_labels": [],
            },
            "sentry": {
                "url": GMAIL2S3_SENTRY_URL,
                "environment": GMAIL2S3_SENTRY_ENV,
            },
        }

        if defaults:
            self.load_conf(defaults)

        if confpath:
            self.load_conffile(confpath)

    @property
    def gmail2s3(self):
        return self.settings["gmail2s3"]

    @property
    def s3(self):
        return self.settings["s3"]

    @property
    def gmail(self):
        return self.settings["gmail"]

    @property
    def sentry(self):
        return self.settings["sentry"]

    def reload(self, confpath, inplace=False):
        if inplace:
            instance = self
            instance.load_conffile(confpath)
        else:
            instance = Gmail2S3Config(defaults=self.settings, confpath=confpath)
        return instance

    def load_conf(self, conf):
        for key, val in conf.items():
            self.settings[key].update(val)

    def load_conffile(self, confpath):
        with open(confpath, "r", encoding="utf-8") as conffile:
            self.load_conf(yaml.safe_load(conffile.read()))


GCONFIG = Gmail2S3Config(confpath=GMAIL2S3_CONF_FILE)
