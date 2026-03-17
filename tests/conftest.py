"""Shared pytest fixtures for CodePulse."""

import pytest

from app import create_app
from models.database import db as _db


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing."""
    application = create_app(testing=True)
    yield application


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a transactional database session for each test."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.drop_all()
