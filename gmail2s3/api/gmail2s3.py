# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging
from copy import deepcopy
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from gmail2s3.gmailauth import (
    MessageQuery,
    Gmail2S3,
    WebHook,
    WebHookBody,
    GmailClient,
)
from gmail2s3.s3 import S3Dest, S3Client
from gmail2s3.config import GCONFIG


router = APIRouter(prefix="/api/v1", tags=["gmail2s3"])
logger = logging.getLogger(__name__)


class SyncedEmail(BaseModel):
    message_id: str = Field("...")
    s3_paths: List = Field([], description="List of path in the S3 bucket")


class SyncedEmailList(BaseModel):
    synced_emails: List[SyncedEmail] = Field("...")
    total: int = Field("...", description="Total number of emails synced to S3")


class S3Conf(BaseModel):
    bucket: str | None = Field(None)
    prefix: str | None = Field(None)


class CopyS3Resp(BaseModel):
    source: S3Dest = Field("...")
    dest: S3Dest = Field("...")


class SyncedEmailRequest(BaseModel):
    query: MessageQuery = Field(MessageQuery())
    webhooks: List[WebHook] = Field([])
    s3conf: S3Conf = Field({})


@router.post("/sync_emails", response_model=SyncedEmailList)
async def sync_emails(req: SyncedEmailRequest) -> SyncedEmailList:
    s3conf = deepcopy(GCONFIG.s3)
    if req.s3conf:
        s3conf.update(req.s3conf.dict(exclude_none=True))
    gmailsyncer = Gmail2S3(
        message_query=req.query, webhooks=req.webhooks, s3conf=s3conf
    )
    resp = gmailsyncer.sync_emails()
    return SyncedEmailList(synced_emails=resp, total=len(resp))


@router.post("/sync_emails_info", response_model=dict)
async def sync_emails_info(req: SyncedEmailRequest) -> dict:
    s3conf = deepcopy(GCONFIG.s3)
    if req.s3conf:
        s3conf.update(req.s3conf.dict(exclude_none=True))
    gmailsyncer = Gmail2S3(
        message_query=req.query, webhooks=req.webhooks, s3conf=s3conf
    )
    resp = gmailsyncer.sync_emails_info()
    return resp


@router.post("/webhooks/upload_attachment/copy", response_model=CopyS3Resp)
async def copy_s3(webhook: WebHookBody) -> CopyS3Resp:
    s3conf = deepcopy(GCONFIG.s3)
    s3_dest_bucket = webhook.params["s3_copy_dest"]["bucket"]
    s3_dest_prefix = webhook.params["s3_copy_dest"]["prefix"]
    s3_src = webhook.payload.s3_uploads[0]
    s3_client = S3Client(s3conf, bucket=s3conf["bucket"])
    resp = s3_client.copy_s3_to_s3(
        src_bucket=s3_src["bucket"],
        src_path=s3_src["path"],
        dest_bucket=s3_dest_bucket,
        dest_prefix=s3_dest_prefix,
    )
    logger.info(resp)
    return CopyS3Resp(source=resp[0], dest=resp[1])


@router.post("/webhooks/griddle-gmail", response_model=dict)
async def griddle_email(webhook: WebHookBody) -> dict:
    griddle_endpoint = webhook.params["email_processor"]["endpoint"]
    raw_message = webhook.payload.message_raw
    message = GmailClient().client._build_message_from_raw_json(raw_message)
    griddle_payload = {
        "to": message.recipient,
        "from": message.sender,
        "cc": message.cc,
        "bcc": message.bcc,
        "html": message.html,
        "text": message.plain,
        "headers_list": message.headers,
        "headers": message.text_headers(),
        "attachments_files": webhook.payload.attachments
    }
    logger.info(griddle_payload)
    return griddle_payload
