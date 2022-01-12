from pathlib import PurePath
from typing import Tuple
import boto3
from botocore.client import Config
from pydantic import BaseModel, Field


class S3Dest(BaseModel):
    bucket: str = Field("...")
    path: str = Field("...")


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

    def __init__(self, options: dict, bucket: str, prefix: str = ""):
        self.options: dict = options
        kwargs: dict = self._boto_args(options)
        self.client = boto3.resource("s3", **kwargs)
        self.bucket: str = bucket
        self.prefix: str = prefix

    def buildpath(self, filename: str, dest: str = ""):
        if not dest:
            dest = PurePath(filename).name
        return f"{self.prefix}{dest}"

    def upload_file(self, filepath: str, dest: str = "") -> S3Dest:
        path = self.buildpath(filepath, dest)
        self.client.Bucket(self.bucket).upload_file(filepath, path)
        return S3Dest(bucket=self.bucket, path=path)

    def copy_s3_to_s3(
        self, src_bucket: str, src_path: str, dest_bucket: str, dest_prefix: str = ""
    ) -> Tuple[S3Dest, S3Dest]:
        copy_source = {
            "Bucket": src_bucket,
            "Key": src_path,
        }

        if not dest_prefix:
            dest_path = src_path
        else:
            dest_path = f"{dest_prefix}{PurePath(src_path).name}"

        self.client.meta.client.copy(copy_source, dest_bucket, dest_path)

        return (
            S3Dest(bucket=src_bucket, path=src_path),
            S3Dest(bucket=dest_bucket, path=dest_path),
        )
