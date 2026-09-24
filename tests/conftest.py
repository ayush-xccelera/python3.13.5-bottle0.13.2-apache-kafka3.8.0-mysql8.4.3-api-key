import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from webtest import TestApp

from app.config import config as app_config
from app.main import app


@pytest.fixture(scope="session")
def test_app():
    return TestApp(app)


@pytest.fixture(scope="session")
def admin_key():
    return app_config.ADMIN_API_KEY
