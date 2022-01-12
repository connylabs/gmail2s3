import json
import pathlib
import logging
from pathlib import PurePath

from datetime import datetime, date
from typing import Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field
from simplegmail import Gmail
from simplegmail.message import Message
from simplegmail.attachment import Attachment
from simplegmail.query import construct_query

from gmail2s3.config import GCONFIG
from gmail2s3.s3 import S3Client, S3Dest
from gmail2s3.client import Gmail2S3Client


logger = logging.getLogger(__name__)


class MessageQuery(BaseModel):
    after: Optional[Union[date, datetime]]
    before: Optional[Union[date, datetime]]
    labels: Optional[List[str]]
    exclude_labels: Optional[List[str]]


class MessageList(BaseModel):
    message_refs: List[Dict]
    query: Optional[MessageQuery]


class WebHookPayload(BaseModel):
    message_ref: dict
    attachments: List[dict]
    s3_uploads: List[dict]


class WebHookBody(BaseModel):
    event: Literal["uploaded_attachment", "synced_email"]
    payload: WebHookPayload
    params: Optional[dict]


class WebHook(BaseModel):
    endpoint: str
    params: Optional[dict] = Field({})
    event: Literal["uploaded_attachment", "synced_email"]
    token: Optional[str] = Field("")
    headers: Optional[dict] = Field({})
    verify_ssl: Optional[bool] = Field(True)

    def trigger_event(
        self, message_ref: dict, attachments: List[Attachment], s3_dests: List[S3Dest]
    ):
        client = Gmail2S3Client(
            self.endpoint,
            token=self.token,
            headers=self.headers,
            requests_verify=self.verify_ssl,
        )

        if self.event == "uploaded_attachment":
            body = WebHookBody(
                event="uploaded_attachment",
                payload=WebHookPayload(
                    message_ref=message_ref,
                    attachments=[attachments[0].dict()],
                    s3_uploads=[s3_dests[0].dict()],
                ),
                params=self.params,
            )

        elif self.event == "synced_email":
            body = WebHookBody(
                event=synced_email,
                payload=WebHookPayload(
                    message_ref=message_ref,
                    attachments=[x.dict() for x in attachments],
                    s3_uploads=[x.dict() for x in s3_dest],
                ),
                params=self.params,
            )
        else:
            raise ValueError(f"unknown event: {self.event}")

        logger.info(f"trigger webhook: {body}")
        resp = client.post(self.endpoint, body=body.dict())
        logger.info(resp.json())
        resp.raise_for_status()
        return resp.status_code


class GmailClient:
    """
    It's assumed that client_secret and gmail_token will be added in the container via secret/configmap
    """

    def __init__(
        self,
        client_secret=GCONFIG.gmail["client_secret"],
        gmail_token=GCONFIG.gmail["gmail_token"],
        dest_dir=GCONFIG.gmail2s3["download_dir"],
    ):
        self.client_secret = client_secret
        self.gmail_token = gmail_token
        self._client = None
        self.dest_dir = dest_dir
        pathlib.Path(self.dest_dir).mkdir(parents=True, exist_ok=True)

    def fetch_token(self):
        """Get the token from an object storage"""
        raise NotImplementedError

    def gen_token(self):
        return self.auth()

    def store_token(self):
        """Upload the gmail_token to an object storage"""
        raise NotImplementedError

    def auth(self):
        print(self.client_secret, self.gmail_token)
        return Gmail(client_secret_file=self.client_secret, creds_file=self.gmail_token)

    @property
    def client(self):
        """
        Initialize the Gmail client if needed.
        In case the creds_file is None, it will prompt the user to consent access
        """
        if self._client is None:
            self._client = self.auth()
        return self._client

    # YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]
    def list_emails(self, message_query: MessageQuery) -> MessageList:
        query_params = {}
        if message_query.labels:
            query_params["labels"] = message_query.labels
        if message_query.exclude_labels:
            query_params["exclude_labels"] = message_query.exclude_labels
        if message_query.after:
            query_params["after"] = message_query.after.strftime("%")
        if message_query.before:
            query_params["before"] = message_query.before.strftime("%s")

        query = construct_query(query_params)
        messages = self.client.get_messages(query=query, refs_only=True)
        MessageList(message_refs=messages, query=message_query)
        return messages

    def pipeline(self):
        """
        - list emails
          for each email:
          trigger job with message_id
            fetch email:
              download attachements
              upload attachements
              upload raw_json
              set label archived-s3
        """
        pass

    def get_email(self, message_ref: dict):
        message = self.client.get_message_from_ref(ref=message_ref)
        return message

    def _message_storage_path(self, message: Message) -> str:
        return str(PurePath().joinpath(message.date.strftime("%Y/%m"), message.id))

    def download_attachements(self, message: Message, overwrite: bool = True):
        paths = []
        for attach in message.attachments:
            fpath = PurePath().joinpath(
                self.dest_dir,
                self._message_storage_path(message),
                "attachements",
                f"{attach.filename}",
            )
            attach.save(str(fpath), overwrite)
            paths.append((str(fpath), attach))
        return paths

    def dump_message(self, message: Message):
        fpath = PurePath().joinpath(
            self.dest_dir, self._message_storage_path(message), f"{message.id}.json"
        )
        return message.dump(fpath)

    def add_labels(self, message: Message, labels: List[str]):
        return message.add_labels(labels)


def _webhooks_dict(webhooks: List[WebHook]) -> dict[str, WebHook]:
    print(webhooks)
    res = {"uploaded_attachment": [], "synced_email": []}
    if webhooks:
        for webh in webhooks:
            res[webh.event].append(webh)
    print(res)
    return res


def gmail2s3(
    message_query: MessageQuery, webhooks: List[WebHook] = [], s3conf: dict = GCONFIG.s3
) -> List[dict]:
    s3 = S3Client(s3conf, bucket=s3conf["bucket"], prefix=s3conf["prefix"])
    gmail = GmailClient()
    message_refs = gmail.list_emails(message_query)
    total = len(message_refs)
    i = 0
    webhooks_h = _webhooks_dict(webhooks)
    synced_emails = []
    for message_ref in message_refs:
        i += 1
        logger.info(f"{message_ref}")
        logger.info(f"synced: {i}/{total}")
        message = gmail.get_email(message_ref)
        attachements = gmail.download_attachements(message)
        s3_dests = []
        for att in attachements:
            fpath, attach = att
            s3_dest = s3.upload_file(
                fpath, str(PurePath(fpath).relative_to(gmail.dest_dir))
            )
            s3_dests.append(s3_dest)
            for webh in webhooks_h["uploaded_attachment"]:
                webh.trigger_event(
                    message_ref, attachments=[attach], s3_dests=[s3_dest]
                )

        raw_message_path = gmail.dump_message(message)
        email_s3_path = s3.upload_file(
            str(raw_message_path), str(raw_message_path.relative_to(gmail.dest_dir))
        )
        s3_dests.append(email_s3_path)
        for webh in webhooks_h["synced_email"]:
            webh.trigger_event(
                message_ref,
                attachments=[att[1] for att in attachments],
                s3_dests=s3_dests,
            )
        gmail.add_labels(message, [gmail.client.get_label_id("s3")])
        synced_emails.append({"message_id": message_ref["id"], "s3_paths": s3_dests})
    return synced_emails
