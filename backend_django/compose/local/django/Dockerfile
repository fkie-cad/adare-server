FROM python:3.10.2-slim-bullseye

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /bin/uv

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # git (needed for uv to install git dependencies)
  && apt-get install -y git \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies via uv.
# --extra test pulls pytest/pytest-django/factory-boy/pytest-cov: this is the
# LOCAL dev image and every `make test*` target runs pytest inside it, so
# without the extra those targets fail with "No module named pytest".
COPY uv.lock pyproject.toml /tmp/
RUN --mount=type=cache,target=/root/.cache/uv \
    cd /tmp && uv sync --locked --no-install-project --extra test

# now exchange django all auth social account models file with /extra/models.py todo: remove this when django all auth fixes the issue
COPY ./extra/models.py /usr/local/lib/python3.10/site-packages/allauth/socialaccount/models.py

COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
