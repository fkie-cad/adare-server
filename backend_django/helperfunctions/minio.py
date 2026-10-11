from functools import lru_cache

import boto3
from django.conf import settings


@lru_cache(maxsize=1)
def _s3_client():
    """Build the MinIO S3 client once per process.

    Creating a boto3 client loads the service model from disk and costs
    milliseconds; the run serializers presign four log URLs per run, so building
    one per call paid that cost four times per rendered run. boto3 clients are
    thread-safe, and presigning is a local signature computation (no network
    round-trip).
    """
    return boto3.client(
        "s3",
        endpoint_url=f'https://{settings.MINIO_ACCESS_URL}',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def get_presigned_url(object_path, expiration=3600):
    """Generate a presigned URL for an object in MinIO."""
    s3_client = _s3_client()

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": object_path},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None