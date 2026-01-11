from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def test_task():
    logger.info("🚀 Celery работает! Автосалон готов к закупкам")
    return "Celery + Django + Docker = SUCCESS!"


@shared_task(bind=True, max_retries=3)
def test_retry_task(self):
    logger.info("Проверяем retry...")
    raise self.retry(countdown=5, exc=ValueError("Тестовый retry"))
