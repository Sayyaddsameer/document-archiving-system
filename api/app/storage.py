import io
import logging
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.config import Settings

logger = logging.getLogger(__name__)


class ObjectStorage:
    """Manages file operations against MinIO object storage."""
    
    def __init__(self, settings: Settings):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        logger.info("MinIO client initialized for endpoint %s", settings.minio_endpoint)
    
    def upload_file(self, key: str, data: BinaryIO, length: int, content_type: str) -> None:
        """Upload a file to the documents bucket."""
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=key,
            data=data,
            length=length,
            content_type=content_type,
        )
        logger.info("Uploaded object %s to bucket %s", key, self.bucket)
    
    def get_file(self, key: str) -> bytes:
        """Download a file from the documents bucket and return its contents."""
        response = None
        try:
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=key,
            )
            return response.read()
        finally:
            if response is not None:
                response.close()
                response.release_conn()
