import os
import logging
import json

import urllib
from urllib.parse import urlparse, ParseResult

import requests

import gmail2s3

logger = logging.getLogger(__name__)
DEFAULT_SERVER = "http://localhost:8080"


# @TODO: Auto generate from schema
class Gmail2S3Client:
    def __init__(
        self,
        endpoint: str = DEFAULT_SERVER,
        token: str = "",
        requests_verify: bool = True,
        headers: dict = {},
    ):
        self.endpoint: ParseResult = self._configure_endpoint(endpoint)
        self.host: str = self.endpoint.geturl()
        self.token = token
        self._headers: dict = {
            "Content-Type": "application/json",
            "User-Agent": f"gmail2s3py-cli/{gmail2s3.__version__}",
        }
        self._headers.update(headers)
        self.verify = requests_verify

    def _url(self, path: str) -> str:
        return self.endpoint.geturl() + path

    def _configure_endpoint(self, endpoint):
        return urlparse(endpoint)

    @property
    def headers(self) -> dict:
        headers: dict = {}
        headers.update(self._headers)
        if self.token:
            headers["Authorization"] = token
        return headers

    def version(self) -> dict:
        path: str = "/version"
        resp = requests.get(self._url(path), headers=self.headers, verify=self.verify)
        resp.raise_for_status()
        return resp.json()

    def _request(self, method, path, params: dict = {}, body: str = "{}"):
        if params:
            path = path + "?" + urllib.urlencode(params)
        return getattr(self.client, method)(
            path,
            data=json.dumps(body),
            headers=headers,
        )

    def get(self, path, params=None, body=None):
        return self._request("get", path, params, body)

    def delete(self, path, params=None, body=None):
        return self._request("delete", path, params, body)

    def post(self, path, params=None, body=None):
        return self._request("post", path, params, body)
