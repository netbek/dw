from enum import StrEnum
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional


class ClickHouseSettings(BaseSettings):
    host: str
    http_port: int
    tcp_port: int
    username: str
    password: str
    database: str
    secure: Optional[bool] = Field(default=False)
    driver: Optional[str] = Field(default=None)

    @property
    def url(self) -> str:
        from package.database import ClickHouseAdapter

        return ClickHouseAdapter.create_url(**self.model_dump(by_alias=True))


class PostgresSettings(BaseSettings):
    host: str
    port: int
    username: str
    password: str
    database: str
    schema_: str = Field(serialization_alias="schema")

    @property
    def url(self) -> str:
        from package.database import PostgresAdapter

        return PostgresAdapter.create_url(**self.model_dump(by_alias=True))


class DbtSettings(BaseSettings):
    directory: Path | str
    config: dict


class PeerDBSettings(BaseSettings):
    config: dict


class PrefectSettings(BaseSettings):
    config: dict


class NotebookSettings(BaseSettings):
    directory: Path | str


class ClickHouseIdentifier:
    @classmethod
    def quote(cls, identifier: str) -> str:
        return f"`{identifier}`"

    @classmethod
    def unquote(cls, identifier: str) -> str:
        return identifier.strip("`")


class ClickHouseTableIdentifier(ClickHouseIdentifier, BaseModel):
    database: Optional[str] = Field(default=None, serialization_alias="database")
    table: str = Field(serialization_alias="table")

    @classmethod
    def from_string(cls, identifier: str) -> "ClickHouseTableIdentifier":
        parts = [cls.unquote(part) for part in identifier.split(".")]

        if len(parts) == 2:
            return cls(database=parts[0], table=parts[1])
        elif len(parts) == 1:
            return cls(table=parts[0])
        else:
            raise ValueError()

    def to_string(self) -> str:
        if self.database is not None:
            return f"{self.quote(self.database)}.{self.quote(self.table)}"
        else:
            return self.quote(self.table)


class PostgresIdentifier:
    @classmethod
    def quote(cls, identifier: str) -> str:
        return f'"{identifier}"'

    @classmethod
    def unquote(cls, identifier: str) -> str:
        return identifier.strip('"')


class PostgresTableIdentifier(PostgresIdentifier, BaseModel):
    database: Optional[str] = Field(default=None, serialization_alias="database")
    schema_: Optional[str] = Field(default=None, serialization_alias="schema")
    table: str = Field(serialization_alias="table")

    @classmethod
    def from_string(cls, identifier: str) -> "PostgresTableIdentifier":
        parts = [cls.unquote(part) for part in identifier.split(".")]

        if len(parts) == 3:
            return cls(database=parts[0], schema_=parts[1], table=parts[2])
        elif len(parts) == 2:
            return cls(schema_=parts[0], table=parts[1])
        elif len(parts) == 1:
            return cls(table=parts[0])
        else:
            raise ValueError()

    def to_string(self) -> str:
        if self.database is not None and self.schema_ is not None:
            return f"{self.quote(self.database)}.{self.quote(self.schema_)}.{self.quote(self.table)}"
        elif self.schema_ is not None:
            return f"{self.quote(self.schema_)}.{self.quote(self.table)}"
        else:
            return self.quote(self.table)


class DbtResourceType(StrEnum):
    MODEL = "model"
    SEED = "seed"
    SOURCE = "source"


class DbtColumnMeta(BaseModel):
    sqlalchemy_type: str


class DbtColumn(BaseModel):
    data_type: str
    meta: Optional[DbtColumnMeta] = None
    name: str


class DbtContract(BaseModel):
    alias_types: bool
    enforced: bool


class DbtDependsOn(BaseModel):
    macros: Optional[List[str]] = None
    nodes: Optional[List[str]] = None


class DbtDocs(BaseModel):
    node_color: Optional[str] = None
    show: bool


class DbtPersistDocs(BaseModel):
    columns: Optional[bool] = None


class DbtTableMeta(BaseModel):
    python_class: str


class DbtTable(BaseModel):
    columns: Optional[List[DbtColumn]] = None
    loaded_at_field: Optional[str] = None
    meta: Optional[DbtTableMeta] = None
    name: str


class DbtBaseResource(BaseModel):
    name: str
    original_file_path: str
    package_name: str
    resource_type: DbtResourceType
    tags: List[str]
    unique_id: str


class DbtModelConfig(BaseModel):
    access: str
    alias: Optional[str] = None
    batch_filter: Optional[str] = None
    batch_size: Optional[int] = None
    column_types: Dict[str, str]
    contract: DbtContract
    database: Optional[str] = None
    docs: DbtDocs
    enabled: bool
    engine: Optional[str] = None
    full_refresh: Optional[bool] = False
    grants: Dict[str, List[str]]
    group: Optional[str] = None
    incremental_strategy: Optional[str] = None
    materialized: str
    meta: Dict[str, str | int | float | bool | None]
    on_configuration_change: str
    on_schema_change: str
    order_by: Optional[str] = None
    packages: List[str]
    persist_docs: DbtPersistDocs
    post_hook: Optional[List[str]] = None
    pre_hook: Optional[List[str]] = None
    quoting: Dict[str, bool]
    range_max: Optional[str] = None
    range_min: Optional[str] = None
    schema_: Optional[str] = Field(default=None, serialization_alias="schema")
    tags: List[str]
    unique_key: Optional[str] = None


class DbtModel(DbtBaseResource):
    alias: str
    config: DbtModelConfig
    depends_on: DbtDependsOn


class DbtSeedConfig(BaseModel):
    alias: Optional[str] = None
    column_types: Dict[str, str]
    contract: DbtContract
    database: Optional[str] = None
    delimiter: str
    docs: DbtDocs
    enabled: bool
    full_refresh: Optional[bool] = False
    grants: Dict[str, List[str]]
    group: Optional[str] = None
    incremental_strategy: Optional[str] = None
    materialized: str
    meta: Dict[str, str | int | float | bool | None]
    on_configuration_change: str
    on_schema_change: str
    packages: List[str]
    persist_docs: DbtPersistDocs
    post_hook: Optional[List[str]] = None
    pre_hook: Optional[List[str]] = None
    quote_columns: Optional[bool] = None
    quoting: Dict[str, bool]
    schema_: Optional[str] = Field(default=None, serialization_alias="schema")
    tags: List[str]
    unique_key: Optional[str] = None


class DbtSeed(DbtBaseResource):
    alias: str
    config: DbtSeedConfig
    depends_on: DbtDependsOn


class DbtSourceConfig(BaseModel):
    enabled: bool


class DbtSource(DbtBaseResource):
    config: DbtSourceConfig
    original_config: Optional[DbtTable] = None
    source_name: str
