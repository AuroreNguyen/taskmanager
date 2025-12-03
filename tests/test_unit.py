import pytest
from datetime import date, timedelta
import os
import sys
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Task, User
from app import _build_postgres_uri


def test_task_is_overdue_logic():

    today = date.today()

    past_date = today - timedelta(days=1)
    overdue_task = Task(due_date=past_date, is_completed=False)
    assert overdue_task.is_overdue() is True

    today_task = Task(due_date=today, is_completed=False)
    assert today_task.is_overdue() is False

    completed_task = Task(due_date=past_date, is_completed=True)
    assert completed_task.is_overdue() is False

def test_user_password_hashing():

    user = User(username="testuser")
    raw_password = "SecurePassword123"

    user.set_password(raw_password)

    assert user.password_hash is not None
    assert user.password_hash != raw_password

    assert user.check_password(raw_password) is True

    assert user.check_password("WrongPassword") is False

@patch.dict(os.environ, {}, clear=True)
def test_build_postgres_uri_with_defaults():

    expected_uri = "postgresql+psycopg2://postgres:postgres@localhost:5432/taskmanager"
    assert _build_postgres_uri() == expected_uri

@patch.dict(
    os.environ,
    {
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_HOST": "db.example.com",
        "POSTGRES_PORT": "5433",
        "POSTGRES_DB": "prod_db",
    },
    clear=True,
)
def test_build_postgres_uri_with_custom_vars():
    
    expected_uri = "postgresql+psycopg2://test_user:test_password@db.example.com:5433/prod_db"
    assert _build_postgres_uri() == expected_uri

@patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg2://ci:ci@cihost:5432/ci_db"}, clear=True)
def test_build_postgres_uri_with_database_url():
    
    expected_uri = "postgresql+psycopg2://ci:ci@cihost:5432/ci_db"
    assert _build_postgres_uri() == expected_uri