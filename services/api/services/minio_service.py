"""
MinIO service for object storage
"""
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import structlog
from config import settings
from typing import Optional
from datetime import timedelta

logger = structlog.get_logger()


class MinIOService:
    """MinIO service wrapper for object storage"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.buckets = settings.MINIO_BUCKETS

    async def initialize_buckets(self):
        """Create MinIO buckets if they don't exist"""
        for bucket in self.buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Failed to create bucket {bucket}: {e}")

    def upload_file(self, bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload file to MinIO"""
        try:
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded object: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload object: {e}", bucket=bucket, object=object_name)
            return False

    def download_file(self, bucket: str, object_name: str) -> Optional[bytes]:
        """Download file from MinIO"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to download object: {e}", bucket=bucket, object=object_name)
            return None

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """Generate presigned URL for object"""
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}", bucket=bucket, object=object_name)
            return None

    def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete file from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted object: {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete object: {e}", bucket=bucket, object=object_name)
            return False

    def list_objects(self, bucket: str, prefix: str = "") -> list:
        """List objects in bucket"""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}", bucket=bucket)
            return []

    async def store_html_snapshot(self, company_id: int, url: str, html: str) -> str:
        """Store HTML snapshot"""
        object_name = f"company_{company_id}/{url.replace('/', '_').replace(':', '_')}.html"
        success = self.upload_file(
            "raw-html",
            object_name,
            html.encode('utf-8'),
            content_type="text/html"
        )
        if success:
            return f"minio://raw-html/{object_name}"
        return ""

    async def store_proposal_pdf(self, proposal_id: int, pdf_data: bytes) -> str:
        """Store proposal PDF"""
        object_name = f"proposal_{proposal_id}.pdf"
        success = self.upload_file(
            "proposals",
            object_name,
            pdf_data,
            content_type="application/pdf"
        )
        if success:
            return f"minio://proposals/{object_name}"
        return ""

    async def get_proposal_pdf_url(self, proposal_id: int) -> Optional[str]:
        """Get presigned URL for proposal PDF"""
        object_name = f"proposal_{proposal_id}.pdf"
        return self.get_presigned_url("proposals", object_name)


# Global instance
minio_client = MinIOService()
