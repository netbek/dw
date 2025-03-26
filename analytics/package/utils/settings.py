from package.types import (
    ClickHouseSettings,
    DbtSettings,
    NotebookSettings,
    PeerDBSettings,
    PostgresSettings,
    PrefectSettings,
)
from package.utils.template import render_jinja_template
from package.utils.yaml_utils import safe_load_file
from pathlib import Path
from pydantic import Field
from pydantic_settings import SettingsConfigDict

import yaml


def create_postgres_settings(env_prefix: str) -> PostgresSettings:
    class Settings(PostgresSettings):
        model_config = SettingsConfigDict(
            env_file="/usr/local/share/dw/database.env", extra="ignore"
        )

        host: str = Field(
            validation_alias=f"{env_prefix}host",
            serialization_alias="host",
        )
        port: int = Field(
            validation_alias=f"{env_prefix}port",
            serialization_alias="port",
        )
        username: str = Field(
            validation_alias=f"{env_prefix}username",
            serialization_alias="username",
        )
        password: str = Field(
            validation_alias=f"{env_prefix}password",
            serialization_alias="password",
        )
        database: str = Field(
            validation_alias=f"{env_prefix}database",
            serialization_alias="database",
        )
        schema_: str = Field(
            validation_alias=f"{env_prefix}schema",
            serialization_alias="schema",
        )

    return Settings


def create_clickhouse_settings(env_prefix: str) -> ClickHouseSettings:
    class Settings(ClickHouseSettings):
        model_config = SettingsConfigDict(
            env_file="/usr/local/share/dw/database.env", extra="ignore"
        )

        host: str = Field(
            validation_alias=f"{env_prefix}host",
            serialization_alias="host",
        )
        http_port: int = Field(
            validation_alias=f"{env_prefix}http_port",
            serialization_alias="http_port",
        )
        tcp_port: int = Field(
            validation_alias=f"{env_prefix}tcp_port",
            serialization_alias="tcp_port",
        )
        username: str = Field(
            validation_alias=f"{env_prefix}username",
            serialization_alias="username",
        )
        password: str = Field(
            validation_alias=f"{env_prefix}password",
            serialization_alias="password",
        )
        database: str = Field(
            validation_alias=f"{env_prefix}database",
            serialization_alias="database",
        )
        secure: bool = Field(
            validation_alias=f"{env_prefix}secure",
            serialization_alias="secure",
        )
        driver: str = Field(
            validation_alias=f"{env_prefix}driver",
            serialization_alias="driver",
        )

    return Settings


def create_dbt_settings(directory: Path | str, config_path: Path | str) -> DbtSettings:
    class Settings(DbtSettings):
        directory: Path | str = Field(default_factory=lambda: directory)
        config: dict = Field(default_factory=lambda: safe_load_file(config_path))

    return Settings


def create_notebook_settings(directory: Path | str) -> NotebookSettings:
    class Settings(NotebookSettings):
        directory: Path | str = Field(default_factory=lambda: directory)

    return Settings


def create_peerdb_settings(config_path: Path | str) -> PeerDBSettings:
    class Settings(PeerDBSettings):
        model_config = SettingsConfigDict(
            env_file="/usr/local/share/dw/peerdb.env", extra="ignore"
        )

        api_url: str = Field(validation_alias="peerdb_api_url")
        config: dict = Field(
            default_factory=lambda: yaml.safe_load(render_jinja_template(config_path))
        )

    return Settings


def create_prefect_settings(config_path: Path | str) -> PrefectSettings:
    class Settings(PrefectSettings):
        config: dict = Field(default_factory=lambda: safe_load_file(config_path))

    return Settings
