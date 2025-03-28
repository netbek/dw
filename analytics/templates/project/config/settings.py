from functools import lru_cache
from package.project import Project
from package.types import ClickHouseSettings, PostgresSettings
from package.utils.settings import create_clickhouse_settings, create_postgres_settings
from package.utils.yaml_utils import safe_load_file
from pydantic import BaseModel, Field

project = Project.from_path(__file__)


class Settings(BaseModel):
    source_db: PostgresSettings = Field(
        default_factory=create_postgres_settings("source_postgres_")
    )
    destination_db: ClickHouseSettings = Field(
        default_factory=create_clickhouse_settings(f"{project.name}_destination_")
    )
    dbt: dict = Field(default_factory=lambda: safe_load_file(project.dbt_config_path))
    prefect: dict = Field(default_factory=lambda: safe_load_file(project.prefect_config_path))


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
