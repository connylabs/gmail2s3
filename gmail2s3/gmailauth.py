import pathlib
import logging
import time
from pathlib import PurePath
from enum import Enum
from datetime import datetime, date
from typing import Dict, List, Tuple, Any

from pydantic import BaseModel, Field
from simplegmail import Gmail
from simplegmail.message import Message
from simplegmail.attachment import Attachment
from simplegmail.query import construct_query

from gmail2s3.config import GCONFIG
from gmail2s3.s3 import S3Client, S3Dest
from gmail2s3.client import Gmail2S3Client


logger = logging.getLogger(__name__)


class WebHookType(str, Enum):
    SYNCED_EMAIL = "synced_email"
    UPLOADED_ATTACHMENT = "uploaded_attachment"
    SYNC_COMPLETED = "sync_completed"


class MessageQuery(BaseModel):
    after: date | datetime | None = Field(None)
    before: date | datetime | None = Field(None)
    labels: List[str] = Field([])
    exclude_labels: List[str] = Field([])
    sender: List[str] = Field([])
    to: List[str] = Field([])


class MessageList(BaseModel):
    message_refs: List[Dict] = Field("...")
    query: MessageQuery | None = Field(None)


class WebHookPayload(BaseModel):
    message_ref: dict = Field("...")
    attachments: List[dict] = Field([])
    s3_uploads: List[dict] = Field([])


class WebHookBody(BaseModel):
    event: WebHookType = Field("...")
    payload: WebHookPayload = Field("...")
    params: dict = Field({})


class WebHook(BaseModel):
    endpoint: str = Field("...")
    params: dict = Field({})
    event: WebHookType = Field("...")
    token: str = Field("")
    headers: dict = Field({})
    verify_ssl: bool = Field(True)

    def trigger_event(
        self, message_ref: dict, attachments: List[Attachment], s3_dests: List[S3Dest]
    ):
        client = Gmail2S3Client(
            self.endpoint,
            token=self.token,
            headers=self.headers,
            requests_verify=self.verify_ssl,
        )

        if self.event == WebHookType.UPLOADED_ATTACHMENT:
            body = WebHookBody(
                event=WebHookType.UPLOADED_ATTACHMENT,
                payload=WebHookPayload(
                    message_ref=message_ref,
                    attachments=[attachments[0].dict()],
                    s3_uploads=[s3_dests[0].dict()],
                ),
                params=self.params,
            )

        elif self.event == WebHookType.SYNCED_EMAIL:
            body = WebHookBody(
                event=WebHookType.SYNCED_EMAIL,
                payload=WebHookPayload(
                    message_ref=message_ref,
                    attachments=[x.dict() for x in attachments],
                    s3_uploads=[x.dict() for x in s3_dests],
                ),
                params=self.params,
            )
        else:
            raise ValueError(f"unknown event: {self.event}")

        logger.info("trigger webhook: %s", body)
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
        logger.info("%s, %s", self.client_secret, self.gmail_token)
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
            query_params["exclude_labels"] = [[x] for x in message_query.exclude_labels]
        if message_query.after:
            query_params["after"] = message_query.after.strftime("%s")
        if message_query.before:
            query_params["before"] = message_query.before.strftime("%s")
        if message_query.sender:
            query_params["sender"] = message_query.sender
        if message_query.to:
            query_params["recipient"] = message_query.to

        query = construct_query(query_params)
        logger.info("Params: %s, query: %s", query_params, str(query))
        messages = self.client.get_messages(query=query, refs_only=True)
        return MessageList(message_refs=messages, query=message_query)

    def get_email(self, message_ref: dict):
        message = self.client.get_message_from_ref(ref=message_ref, with_raw=False)
        return message

    def _message_storage_path(self, message: Message) -> str:
        return str(PurePath().joinpath(message.date.strftime("%Y/%m"), message.id))

    def download_attachments(self, message: Message, overwrite: bool = True):
        paths = []
        for attach in message.attachments:
            fpath = PurePath().joinpath(
                self.dest_dir,
                self._message_storage_path(message),
                "attachments",
                f"{attach.filename}",
            )
            attach.save(str(fpath), overwrite)
            paths.append((str(fpath), attach))
        return paths

    def dump_message(self, message: Message):
        fpath = PurePath().joinpath(
            self.dest_dir, self._message_storage_path(message), f"{message.id}.json"
        )
        message.dump(str(fpath))
        return fpath

    def add_labels(self, message: Message, labels: List[str]):
        return message.add_labels(labels)


class Gmail2S3:
    def __init__(
        self,
        message_query: MessageQuery,
        webhooks: List[WebHook] | None = None,
        s3conf: dict | None = None,
    ):

        self.gmail = GmailClient()
        self.webhooks = self._webhooks_dict(webhooks)
        if not s3conf:
            s3conf = GCONFIG.s3
        self.s3 = S3Client(s3conf, bucket=s3conf["bucket"], prefix=s3conf["prefix"])
        self.message_query = message_query

    @classmethod
    def _webhooks_dict(
        cls, webhooks: List[WebHook] | None
    ) -> dict[WebHookType, List[WebHook]]:
        res: dict[WebHookType, List[WebHook]] = {
            WebHookType.UPLOADED_ATTACHMENT: [],
            WebHookType.SYNCED_EMAIL: [],
            WebHookType.SYNC_COMPLETED: [],
        }

        if webhooks:
            for webh in webhooks:
                res[webh.event].append(webh)
        return res

    def trigger_webhooks(
        self, webhtype: WebHookType, message_ref, attachments, s3_dests
    ):
        for webh in self.webhooks[webhtype]:
            webh.trigger_event(
                message_ref,
                attachments=attachments,
                s3_dests=s3_dests,
            )

    def sync_email(
        self, message_ref: dict, flag_label: str = "s3"
    ) -> Tuple[dict, List[str]]:
        message = self.gmail.get_email(message_ref)
        attachments = self.gmail.download_attachments(message)
        s3_dests = []
        for att in attachments:
            fpath, attach = att
            s3_dest = self.s3.upload_file(
                fpath, str(PurePath(fpath).relative_to(self.gmail.dest_dir))
            )
            s3_dests.append(s3_dest)
            self.trigger_webhooks(
                WebHookType.UPLOADED_ATTACHMENT,
                message_ref,
                attachments=[attach],
                s3_dests=[s3_dest],
            )
        raw_message_path = self.gmail.dump_message(message)
        email_s3_path = self.s3.upload_file(
            str(raw_message_path),
            str(raw_message_path.relative_to(self.gmail.dest_dir)),
        )
        s3_dests.append(email_s3_path)
        self.trigger_webhooks(
            WebHookType.SYNCED_EMAIL,
            message_ref,
            [att[1] for att in attachments],
            s3_dests,
        )
        if flag_label:
            self.gmail.add_labels(message, [self.gmail.client.get_label_id(flag_label)])
        return (message_ref, s3_dests)

    def sync_emails_info(self) -> dict[str, Any]:
        message_list = self.gmail.list_emails(self.message_query)
        return {
            "total": len(message_list.message_refs),
            "query": self.message_query.dict(),
        }

    def sync_emails(self, flag_label: str = "s3") -> List[dict]:
        message_list = self.gmail.list_emails(self.message_query)
        total = len(message_list.message_refs)
        i = 0
        synced_emails = []

        for message_ref in message_list.message_refs:
            i += 1
            logger.info("%s", message_ref)
            logger.info("synced: %s/%s", i, total)
            _, s3_dests = self.sync_email(message_ref, flag_label=flag_label)
            synced_emails.append(
                {"message_id": message_ref["id"], "s3_paths": s3_dests}
            )
        return synced_emails

    def forward_emails(
        self, sender: str, to: str, forward_prefix="[FWD][G2S3] ", flag_label: str = ""
    ) -> List[dict]:
        message_list = self.gmail.list_emails(self.message_query)
        total = len(message_list.message_refs)
        i = 0
        forwarded_emails = []
        for message_ref in message_list.message_refs:
            message = self.gmail.get_email(message_ref)
            self.gmail.client.forward_message(
                message, sender=sender, to=to, forward_prefix=forward_prefix
            )
            i += 1
            logger.info("%s", message_ref)
            logger.info("forwarded: %s/%s", i, total)
            forwarded_emails.append({"message_id": message_ref["id"], "s3_paths": []})
            time.sleep(1)
        return forwarded_emails
