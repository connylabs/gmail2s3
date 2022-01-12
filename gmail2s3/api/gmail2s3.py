# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging
from copy import deepcopy
from typing import Tuple
from fastapi import APIRouter
from pydantic import BaseModel, Field
from gmail2s3.gmailauth import MessageQuery, gmail2s3, MessageList, GmailClient, WebHook

# from gmail2s3.s3 import S3Dest


router = APIRouter(prefix="/api/v1", tags=["gmail2s3"])
logger = logging.getLogger(__name__)


class ResponseExample(BaseModel):
    synced: bool = Field(...)
    path: str = Field(...)
    fstat: str = Field(...)
    request: Item = Field(...)


class SyncedEmail(BaseModel):
    message_id: str
    s3_paths: List[str]


class SyncedEmailList(BaseModel):
    synced_emails: List[SyncedEmail]


class S3Conf(BaseModel):
    bucket: Optional[str]
    prefix: Optional[str]


class SyncedEmailRequest(BaseModel):
    query: Optional[MessageQuery] = Field(MessageQuery())
    webhooks: Optional[List[WebHook]]
    s3conf: Optional[S3Conf]


@router.post("/sync_emails", response_model=SyncedEmailList)
async def sync_emails(req: SyncedEmailRequest) -> SyncedEmailList:
    s3conf = deepcopy(GCONFIG.s3)
    if req.s3conf:
        s3conf.update(req.s3conf)
    return gmail2s3(query=req.query, webhooks=req.webhooks, s3conf=s3conf)


@router.post("/webhooks/upload_attachment/copy", response_model=Tuple(S3Dest, S3Dest))
async def copy_s3(webhook: WebHookBody):
    s3conf = deepcopy(GCONFIG.s3)
    s3_dest_bucket = webhook.params["s3_copy_dest"]["bucket"]
    s3_dest_prefix = webhook.params["s3_copy_dest"]["bucket"]
    s3_src = webhook.payload.s3_uploads[0]
    s3_client = S3Client(s3conf, bucket=s3conf["bucket"])
    return s3_client.copy_s3_to_s3(
        src_bucket=s3_src["bucket"],
        src_path=s3_src["path"],
        dest_bucket=s3_dest_bucket,
        dest_prefix=s3_dest_prefix,
    )
