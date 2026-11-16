"""I test data/ girano dalla root del repo: pytest -q data/tests.

Qui si aggiungono data/ e backend/ al sys.path cosi' gli import `etl.*` e `app.*`
risolvono senza PYTHONPATH. Il fixture `conn` rispecchia backend/tests/conftest.py:
in CI il DB c'e' per forza, saltare sarebbe un falso verde.
"""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "data"))

from app.database import engine  # noqa: E402


@pytest.fixture(scope="session")
def conn():
    try:
        with engine.connect() as c:
            yield c
    except OperationalError:
        if os.getenv("CI"):
            pytest.fail("database non raggiungibile in CI")
        pytest.skip("db spento")
