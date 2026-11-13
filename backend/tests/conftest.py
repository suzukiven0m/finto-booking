import os

import pytest
from sqlalchemy.exc import OperationalError

from app.database import engine


@pytest.fixture(scope="session")
def conn():
    try:
        with engine.connect() as c:
            yield c
    except OperationalError:
        # In CI il database c'e' per forza: saltare renderebbe la CI verde
        # senza aver testato niente. In locale invece lo skip va bene.
        if os.getenv("CI"):
            pytest.fail("database non raggiungibile in CI")
        pytest.skip("db spento")
