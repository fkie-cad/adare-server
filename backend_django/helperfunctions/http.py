"""Shared settings for outbound HTTP calls made with ``requests``.

``requests`` has no default timeout, so a stalled Gitea/MinIO peer would hang
the calling gunicorn worker or Celery task forever. Every outbound call passes
``timeout=HTTP_TIMEOUT`` -- (connect, read) seconds. The read timeout bounds the
gap between received bytes, not the whole transfer, so streamed downloads of
large files are unaffected.
"""

HTTP_TIMEOUT = (5, 30)
