from pathlib import PurePath

import boto3
from botocore.client import Config

from gmail2s3.config import GCONFIG


class S3Client:
    def _boto_args(self, options: dict):
        kwargs: dict = {}
        if options["endpoint"]:
            kwargs["endpoint_url"] = options["endpoint"]
        if options["region"]:
            kwargs["region_name"] = options["region"]
        kwargs["aws_access_key_id"] = options["access_key"]
        kwargs["aws_secret_access_key"] = options["secret_key"]
        kwargs["config"] = Config(signature_version="s3v4")
        return kwargs

    def __init__(self, options: dict, bucket: str, prefix: str=''):
        self.options: dict = options
        kwargs: dict = self._boto_args(options)
        self.client = boto3.resource("s3", **kwargs)
        self.bucket: str = bucket
        self.prefix: str = prefix

    def buildpath(self, filename: str, dest: str=''):
        if not dest:
            dest = PurePath(filename).name
        return f"{self.prefix}dest"

    def upload_file(self, filepath: str, dest: str=''):
        s3.Bucket(self.bucket).upload_file(filepath, self.buildpath(filepath, dest))
