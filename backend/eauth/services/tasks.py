from celery.utils.log import get_task_logger

from backend.celery import app

logger = get_task_logger(__name__)
