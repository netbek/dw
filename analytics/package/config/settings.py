from functools import lru_cache
from package.types import ClickHouseSettings, PostgresSettings
from package.utils.settings import create_clickhouse_settings, create_postgres_settings
from pydantic import BaseModel, Field


class Settings(BaseModel):
    test_clickhouse: ClickHouseSettings = Field(
        default_factory=create_clickhouse_settings("package_test_clickhouse_"),
    )
    test_postgres: PostgresSettings = Field(
        default_factory=create_postgres_settings("package_test_postgres_"),
    )


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
