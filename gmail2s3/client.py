import os
import logging

import requests
from requests.utils import urlparse

import gmail2s3

logger = logging.getLogger(__name__)
DEFAULT_SERVER = "http://localhost:8080"


# @TODO: Auto generate from schema
class Gmail2S3Client:
    def __init__(self, endpoint=DEFAULT_SERVER, requests_verify=True):
        self.endpoint = self._configure_endpoint(endpoint)
        self.host = self.endpoint.geturl()
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": "gmail2s3py-cli/%s" % gmail2s3.__version__,
        }

        if "GMAIL2S3_CA_BUNDLES" in os.environ:
            requests_verify = os.environ["GMAIL2S3_CA_BUNDLES"]
        if requests_verify is None:
            requests_verify = True
        self.verify = requests_verify

    def _url(self, path):
        return self.endpoint.geturl() + path

    def _configure_endpoint(self, endpoint):
        return urlparse(endpoint)

    @property
    def headers(self):
        token = None
        headers = {}
        headers.update(self._headers)
        if token is not None:
            headers["Authorization"] = token
        return headers

    def version(self):
        path = "/version"
        resp = requests.get(self._url(path), headers=self.headers, verify=self.verify)
        resp.raise_for_status()
        return resp.json()
