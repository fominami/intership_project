# tests/conftest.py — ТОЛЬКО БАЗОВЫЕ ФИКСТУРЫ!
import pytest
from rest_framework.test import APIClient
from celery import current_app


@pytest.fixture(autouse=True)
def enable_db_access(db):
    """Доступ к БД"""
    pass


@pytest.fixture
def api_client():
    """DRF клиент"""
    return APIClient()


@pytest.fixture(autouse=True)
def celery_eager():
    """Celery синхронно"""
    current_app.conf.task_always_eager = True
    yield
    current_app.conf.task_always_eager = False
