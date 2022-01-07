import json
import pathlib
from pathlib import PurePath

from datetime import datetime
from typing import Deque, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from pydantic import BaseModel, Field
from simplegmail import Gmail
from simplegmail.message import Message
from simplegmail.query import construct_query

from gmail2s3.config import GCONFIG
from gmail2s3.s3 import S3Client


class MessageQuery(BaseModel):
    startDate: datetime
    endDate: datetime
    labels: List[str]


class MessageList(BaseModel):
    messageIds: List[str]
    userId: str = Field(...)
    query: MessageQuery


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
    def list_emails(
        self,
        after: str = "",
        before: str = "",
        labels: List[List[str]] = [],
        exclude_labels: List[List[str]] = [],
    ) -> MessageList:

        query_params = {}
        if labels:
            query_params["labels"] = labels
        if exclude_labels:
            query_params["exclude_labels"] = exclude_labels
        if after:
            query_params["after"] = datetime.fromisoformat(after).strftime("%s")
        if before:
            query_params["before"] = datetime.fromisoformat(before).strftime("%s")

        query = construct_query(query_params)
        messages = self.client.get_messages(query=query, refs_only=True)
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
            paths.append(str(fpath))
        return paths

    def dump_message(self, message: Message):
        fpath = PurePath().joinpath(
            self.dest_dir, self._message_storage_path(message), f"{message.id}.json"
        )
        return message.dump(fpath)

    def add_labels(self, message: Message, labels: List[str]):
        return message.add_labels(labels)


def gmail2s3(
    s3: dict = GCONFIG.s3,
    after: str = "2022-01-01",
    before: str = "",
    labels: List[List[str]] = GCONFIG.gmail["in_labels"],
    exclude_labels: List[List[str]] = GCONFIG.gmail["out_labels"],
):
    # s3_label_id = 'Label_4009252254966186696'
    s3 = S3Client(s3, bucket=s3["bucket"], prefix=s3["prefix"])
    gmail = GmailClient()
    message_refs = gmail.list_emails(after, before, labels, exclude_labels)
    total = len(message_refs)
    i = 0
    for message_ref in message_refs:
        i += 1
        print(f"{message_ref}")
        print(f"synced: {i}/{total}")
        message = gmail.get_email(message_ref)
        print(message.date)
        attachements = gmail.download_attachements(message)
        for fpath in attachements:
            s3.upload_file(fpath, str(PurePath(fpath).relative_to(gmail.dest_dir)))
            gmail.add_labels(message, [gmail.client.get_label_id("s3")])
        raw_message_path = gmail.dump_message(message)
        s3.upload_file(
            str(raw_message_path), str(raw_message_path.relative_to(gmail.dest_dir))
        )
