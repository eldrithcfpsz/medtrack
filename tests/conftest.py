import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database
import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A Flask test client backed by a fresh, isolated SQLite database."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setattr(database, 'DATABASE', str(db_path))
    database.init_db()

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as client:
        yield client


def register(client, username, password):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=False,
    )


def login(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=False,
    )


@pytest.fixture
def user_client(client):
    """A client logged in as a regular (non-admin) user named 'alice'."""
    register(client, 'alice', 'password123')
    return client


def add_med(client, name='Aspirin', dosage='500mg', frequency='2', stock='10', notes=''):
    return client.post(
        '/add',
        data={
            'name': name,
            'dosage': dosage,
            'frequency': frequency,
            'stock': stock,
            'notes': notes,
        },
        follow_redirects=False,
    )
