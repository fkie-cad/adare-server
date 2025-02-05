import boto3
from django.conf import settings

def get_presigned_url(object_path, expiration=3600):
    # print(object_path)
    # url = f'https://{settings.MINIO_ACCESS_URL}'
    # object_name = object_path.split(url)[1]

    """Generate a presigned URL for an object in MinIO."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=f'https://{settings.MINIO_ACCESS_URL}',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

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