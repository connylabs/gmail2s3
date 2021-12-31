import os
import logging
from urllib.parse import urlparse, ParseResult

import requests


import gmail2s3

logger = logging.getLogger(__name__)
DEFAULT_SERVER = "http://localhost:8080"


# @TODO: Auto generate from schema
class Gmail2S3Client:
    def __init__(self, endpoint: str = DEFAULT_SERVER, requests_verify: bool = True):
        self.endpoint: ParseResult = self._configure_endpoint(endpoint)
        self.host: str = self.endpoint.geturl()
        self._headers: dict = {
            "Content-Type": "application/json",
            "User-Agent": f"gmail2s3py-cli/{gmail2s3.__version__}",
        }
        self.verify = requests_verify

    def _url(self, path: str) -> str:
        return self.endpoint.geturl() + path

    def _configure_endpoint(self, endpoint):
        return urlparse(endpoint)

    @property
    def headers(self) -> dict:
        token: str = ''
        headers: dict = {}
        headers.update(self._headers)
        if token:
            headers["Authorization"] = token
        return headers

    def version(self) -> dict:
        path: str = "/version"
        resp = requests.get(self._url(path), headers=self.headers, verify=self.verify)
        resp.raise_for_status()
        return resp.json()
