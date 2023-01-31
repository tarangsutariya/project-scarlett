
from app import make_celery
celery = make_celery()
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
@celery.task
def tasktestq():
    logger.info("THIS IS QUEUE 1")
