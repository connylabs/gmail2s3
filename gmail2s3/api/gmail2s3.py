# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging
from copy import deepcopy
from typing import Tuple, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from gmail2s3.gmailauth import (
    MessageQuery,
    Gmail2S3,
    WebHook,
    WebHookBody,
)
from gmail2s3.s3 import S3Dest, S3Client
from gmail2s3.config import GCONFIG


router = APIRouter(prefix="/api/v1", tags=["gmail2s3"])
logger = logging.getLogger(__name__)


class SyncedEmail(BaseModel):
    message_id: str
    s3_paths: Optional[List[str]]


class SyncedEmailList(BaseModel):
    synced_emails: List[SyncedEmail]


class S3Conf(BaseModel):
    bucket: Optional[str]
    prefix: Optional[str]


class SyncedEmailRequest(BaseModel):
    query: Optional[MessageQuery] = Field(MessageQuery())
    webhooks: Optional[List[WebHook]] = Field([])
    s3conf: Optional[S3Conf] = Field({})


@router.post("/sync_emails", response_model=list[dict])
async def sync_emails(req: SyncedEmailRequest) -> list[dict]:
    s3conf = deepcopy(GCONFIG.s3)
    if req.s3conf:
        s3conf.update(req.s3conf)
    gmailsyncer = Gmail2S3(
        message_query=req.query, webhooks=req.webhooks, s3conf=s3conf
    )
    gmailsyncer.sync_emails()


@router.post("/webhooks/upload_attachment/copy", response_model=Tuple[S3Dest, S3Dest])
async def copy_s3(webhook: WebHookBody):
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
    return resp
