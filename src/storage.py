"""AWS S3 storage helpers — gracefully no-ops when credentials are not configured."""

import os
from typing import Optional

from loguru import logger

try:
    import boto3
    _boto3_available = True
except ImportError:
    _boto3_available = False

_s3_client = None

BUCKET = os.getenv("AWS_S3_BUCKET", "")


def _client():
    global _s3_client
    if _s3_client is None:
        if not _boto3_available:
            return None
        key = os.getenv("AWS_ACCESS_KEY_ID", "")
        secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        if not key or not secret or key.startswith("your_"):
            return None
        try:
            _s3_client = boto3.client(
                "s3",
                aws_access_key_id=key,
                aws_secret_access_key=secret,
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
        except Exception as exc:
            logger.warning(f"S3 client init failed: {exc}")
    return _s3_client


def upload_bytes(data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> Optional[str]:
    """Upload bytes to S3 and return the public URL, or None if S3 is not configured."""
    client = _client()
    bucket = BUCKET or os.getenv("AWS_S3_BUCKET", "")
    if not client or not bucket:
        return None
    try:
        client.put_object(Bucket=bucket, Key=s3_key, Body=data, ContentType=content_type)
        url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
        logger.info(f"Uploaded to S3: {s3_key}")
        return url
    except Exception as exc:
        logger.warning(f"S3 upload failed: {exc}")
        return None


def delete_object(s3_key: str) -> bool:
    """Delete an object from S3. Returns True on success, False otherwise."""
    client = _client()
    bucket = BUCKET or os.getenv("AWS_S3_BUCKET", "")
    if not client or not bucket or not s3_key:
        return False
    try:
        client.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(f"Deleted from S3: {s3_key}")
        return True
    except Exception as exc:
        logger.warning(f"S3 delete failed: {exc}")
        return False


def presigned_url(s3_key: str, expiry: int = 3600) -> Optional[str]:
    """Generate a pre-signed download URL valid for `expiry` seconds."""
    client = _client()
    bucket = BUCKET or os.getenv("AWS_S3_BUCKET", "")
    if not client or not bucket or not s3_key:
        return None
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )
    except Exception as exc:
        logger.warning(f"Pre-signed URL failed: {exc}")
        return None
