from celery import Celery
from celery.signals import setup_logging
from celery.utils.log import get_task_logger

app = Celery('adare')
app.config_from_object('django.conf:settings', namespace='CELERY')


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings

    dictConfig(settings.LOGGING)


app.autodiscover_tasks()

celery_log = get_task_logger(__name__)
