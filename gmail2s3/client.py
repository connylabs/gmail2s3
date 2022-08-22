import logging
import json
from typing import Mapping
from urllib.parse import urlparse, ParseResult, urlencode

import requests

import gmail2s3

logger = logging.getLogger(__name__)
DEFAULT_SERVER = "http://localhost:8080"


class Gmail2S3Client:
    def __init__(
        self,
        endpoint: str = DEFAULT_SERVER,
        token: str = "",
        requests_verify: bool = True,
        headers: Mapping | None = None,
    ):
        self.endpoint: ParseResult = self._configure_endpoint(endpoint)
        self.host: str = self.endpoint.geturl()
        self.token = token
        self._headers: dict = {
            "Content-Type": "application/json",
            "User-Agent": f"gmail2s3py-cli/{gmail2s3.__version__}",
        }
        if headers:
            self._headers.update(headers)
        self.verify = requests_verify

    def _url(self, path: str) -> str:
        return self.endpoint.geturl() + path

    @staticmethod
    def _configure_endpoint(endpoint):
        return urlparse(endpoint)

    @property
    def headers(self) -> dict:
        headers: dict = {}
        headers.update(self._headers)
        if self.token:
            headers["Authorization"] = self.token
        return headers

    def version(self) -> dict:
        path: str = "/version"
        resp = requests.get(self._url(path), headers=self.headers, verify=self.verify)
        resp.raise_for_status()
        return resp.json()

    def _request(self, method, path, params: dict | None = None, body: str = "{}"):
        if params:
            path = path + "?" + urlencode(params)
        return getattr(requests, method)(
            path,
            data=json.dumps(body),
            headers=self.headers,
        )

    def get(self, path, params=None, body=None):
        return self._request("get", path, params, body)

    def delete(self, path, params=None, body=None):
        return self._request("delete", path, params, body)

    def post(self, path, params=None, body=None):
        return self._request("post", path, params, body)
