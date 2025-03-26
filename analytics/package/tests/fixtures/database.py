from package.config.settings import get_settings
from package.database import ClickHouseAdapter, PostgresAdapter
from sqlmodel import Session
from typing import Any, Generator

import pytest

settings = get_settings()


class DatabaseTest:
    @pytest.fixture(scope="session")
    def clickhouse_adapter(self) -> Generator[ClickHouseAdapter, Any, None]:
        yield ClickHouseAdapter(settings.test_clickhouse)

    @pytest.fixture(scope="function")
    def clickhouse_session(
        self, clickhouse_adapter: ClickHouseAdapter
    ) -> Generator[Session, Any, None]:
        with clickhouse_adapter.create_engine() as engine:
            session = Session(engine)

        yield session

        session.close()

    @pytest.fixture(scope="session")
    def postgres_adapter(self) -> Generator[PostgresAdapter, Any, None]:
        yield PostgresAdapter(settings.test_postgres)
