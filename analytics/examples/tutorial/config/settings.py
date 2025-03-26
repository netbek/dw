from functools import lru_cache
from package.project import Project
from package.types import (
    ClickHouseSettings,
    DbtSettings,
    NotebookSettings,
    PostgresSettings,
    PrefectSettings,
)
from package.utils.settings import (
    create_clickhouse_settings,
    create_dbt_settings,
    create_notebook_settings,
    create_postgres_settings,
    create_prefect_settings,
)
from pydantic import BaseModel, Field

# from package.types import PeerDBSettings
# from package.utils.settings import create_peerdb_settings

project = Project.from_path(__file__)


class Settings(BaseModel):
    source_db: PostgresSettings = Field(
        default_factory=create_postgres_settings("source_postgres_")
    )
    destination_db: ClickHouseSettings = Field(
        default_factory=create_clickhouse_settings(f"{project.name}_destination_")
    )
    dbt: DbtSettings = Field(
        default_factory=create_dbt_settings(
            project.dbt_directory, project.dbt_config_path
        )
    )
    notebook: NotebookSettings = Field(
        default_factory=create_notebook_settings(project.notebooks_directory)
    )
    # peerdb: PeerDBSettings = Field(
    #     default_factory=create_peerdb_settings(project.peerdb_config_path)
    # )
    prefect: PrefectSettings = Field(
        default_factory=create_prefect_settings(project.prefect_config_path)
    )


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
