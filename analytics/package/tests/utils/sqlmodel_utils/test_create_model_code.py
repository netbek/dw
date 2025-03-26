from package.config.settings import get_settings
from package.database import ClickHouseAdapter
from package.tests.fixtures.database import DatabaseTest
from package.types import ClickHouseTableIdentifier, DbtSource
from package.utils.sqlmodel_utils import create_model_code
from sqlmodel import Table
from typing import Any, Generator

import pytest

settings = get_settings()

table = "test_table"
table_identifier = ClickHouseTableIdentifier(
    database=settings.test_clickhouse.database, table=table
)
python_class = "TestTable"

create_table_statement = f"""
create or replace table {table_identifier.to_string()}
(
    `uint64` UInt64,
    `int64` Int64,
    `uint32` UInt32,
    `int32` Int32,
    `uint16` UInt16,
    `int16` Int16,
    `uint8` UInt8,
    `int8` Int8,
    `float64` Float64,
    `float32` Float32,
    `bool` Boolean,
    `nullable_bool` Nullable(Boolean),
    `date32` Date32,
    `datetime` DateTime default now(),
    `nullable(datetime)` Nullable(DateTime),
    `datetime64` DateTime64(9) default now(),
    `nullable_datetime64` Nullable(DateTime64(9)),
    `string` String,
    `nullable_string` Nullable(String),
    `uuid` UUID,
    `nullable_uuid` Nullable(UUID),
    `_peerdb_synced_at` DateTime64(9) DEFAULT now64(),
    `_peerdb_is_deleted` Int8,
    `_peerdb_version` Int64
)
engine = MergeTree
primary key `uint64`
order by `uint64`
"""

dbt_source = {
    "name": table_identifier.table,
    "resource_type": "source",
    "package_name": "test",
    "original_file_path": "models/sources.yml",
    "unique_id": f"source.test.{table_identifier.database}.{table_identifier.table}",
    "source_name": table_identifier.database,
    "tags": [],
    "config": {"enabled": True},
    "original_config": {
        "name": table_identifier.table,
        "meta": {
            "python_class": python_class,
        },
        "columns": [
            {"name": "uint64", "data_type": "UInt64"},
            {"name": "int64", "data_type": "Int64"},
            {"name": "uint32", "data_type": "UInt32"},
            {"name": "int32", "data_type": "Int32"},
            {"name": "uint16", "data_type": "UInt16"},
            {"name": "int16", "data_type": "Int16"},
            {"name": "uint8", "data_type": "UInt8"},
            {"name": "int8", "data_type": "Int8"},
            {"name": "float64", "data_type": "Float64"},
            {"name": "float32", "data_type": "Float32"},
            {"name": "bool", "data_type": "Boolean"},
            {"name": "nullable_bool", "data_type": "Nullable(Boolean)"},
            {"name": "date32", "data_type": "Date32"},
            {"name": "datetime", "data_type": "DateTime"},
            {"name": "nullable_datetime", "data_type": "Nullable(DateTime)"},
            {"name": "datetime64", "data_type": "DateTime64(9)"},
            {"name": "nullable_datetime64", "data_type": "Nullable(DateTime64(9))"},
            {"name": "string", "data_type": "String"},
            {"name": "nullable_string", "data_type": "Nullable(String)"},
            {"name": "uuid", "data_type": "UUID"},
            {"name": "nullable_uuid", "data_type": "Nullable(UUID)"},
            {"name": "_peerdb_synced_at", "data_type": "DateTime64(9)"},
            {"name": "_peerdb_is_deleted", "data_type": "Int8"},
            {"name": "_peerdb_version", "data_type": "Int64"},
        ],
    },
}
dbt_source = DbtSource(**dbt_source)

expected_model_code = f"""
\"""
Created from:

CREATE TABLE {table_identifier.database}.{table_identifier.table}
(
    `uint64` UInt64,
    `int64` Int64,
    `uint32` UInt32,
    `int32` Int32,
    `uint16` UInt16,
    `int16` Int16,
    `uint8` UInt8,
    `int8` Int8,
    `float64` Float64,
    `float32` Float32,
    `bool` Bool,
    `nullable_bool` Nullable(Bool),
    `date32` Date32,
    `datetime` DateTime DEFAULT now(),
    `nullable(datetime)` Nullable(DateTime),
    `datetime64` DateTime64(9) DEFAULT now(),
    `nullable_datetime64` Nullable(DateTime64(9)),
    `string` String,
    `nullable_string` Nullable(String),
    `uuid` UUID,
    `nullable_uuid` Nullable(UUID),
    `_peerdb_synced_at` DateTime64(9) DEFAULT now64(),
    `_peerdb_is_deleted` Int8,
    `_peerdb_version` Int64
)
ENGINE = MergeTree
PRIMARY KEY uint64
ORDER BY uint64
SETTINGS index_granularity = 8192
\"""

from clickhouse_sqlalchemy import engines
from package.polyfactory.mixins import BaseMixin
from package.sqlalchemy.clickhouse import types
from sqlmodel import Column, Field, SQLModel
from uuid import UUID
import datetime


class {python_class}(BaseMixin, SQLModel, table=True):
    __tablename__ = '{table_identifier.table}'
    __table_args__ = (engines.MergeTree(order_by=('uint64',), primary_key=('uint64',), index_granularity=8192), {{'schema': '{table_identifier.database}'}},)

    uint64: int = Field(sa_column=Column(name='uint64', type_=types.UInt64, primary_key=True))
    int64: int = Field(sa_column=Column(name='int64', type_=types.Int64, nullable=False))
    uint32: int = Field(sa_column=Column(name='uint32', type_=types.UInt32, nullable=False))
    int32: int = Field(sa_column=Column(name='int32', type_=types.Int32, nullable=False))
    uint16: int = Field(sa_column=Column(name='uint16', type_=types.UInt16, nullable=False))
    int16: int = Field(sa_column=Column(name='int16', type_=types.Int16, nullable=False))
    uint8: int = Field(sa_column=Column(name='uint8', type_=types.UInt8, nullable=False))
    int8: int = Field(sa_column=Column(name='int8', type_=types.Int8, nullable=False))
    float64: float = Field(sa_column=Column(name='float64', type_=types.Float64, nullable=False))
    float32: float = Field(sa_column=Column(name='float32', type_=types.Float32, nullable=False))
    bool: bool = Field(sa_column=Column(name='bool', type_=types.Boolean, nullable=False))
    nullable_bool: bool | None = Field(sa_column=Column(name='nullable_bool', type_=types.Nullable(types.Boolean), nullable=True))
    date32: datetime.date = Field(sa_column=Column(name='date32', type_=types.Date32, nullable=False))
    datetime: datetime.datetime = Field(sa_column=Column(name='datetime', type_=types.DateTime, nullable=False))
    nullable(datetime): datetime.datetime | None = Field(sa_column=Column(name='nullable(datetime)', type_=types.Nullable(types.DateTime), nullable=True))
    datetime64: datetime.datetime = Field(sa_column=Column(name='datetime64', type_=types.DateTime64(9), nullable=False))
    nullable_datetime64: datetime.datetime | None = Field(sa_column=Column(name='nullable_datetime64', type_=types.Nullable(types.DateTime64(9)), nullable=True))
    string: str = Field(sa_column=Column(name='string', type_=types.String, nullable=False))
    nullable_string: str | None = Field(sa_column=Column(name='nullable_string', type_=types.Nullable(types.String), nullable=True))
    uuid: UUID = Field(sa_column=Column(name='uuid', type_=types.UUID, nullable=False))
    nullable_uuid: UUID | None = Field(sa_column=Column(name='nullable_uuid', type_=types.Nullable(types.UUID), nullable=True))
    peerdb_synced_at: datetime.datetime = Field(sa_column=Column(name='_peerdb_synced_at', type_=types.DateTime64(9), nullable=False))
    peerdb_is_deleted: int = Field(sa_column=Column(name='_peerdb_is_deleted', type_=types.Int8, nullable=False))
    peerdb_version: int = Field(sa_column=Column(name='_peerdb_version', type_=types.Int64, nullable=False))
"""

expected_factory_code = f"""
from .{table_identifier.table} import {python_class}
from package.polyfactory.factories.sqlmodel_factory import SQLModelFactory
from package.polyfactory.mixins import PeerDBFactoryMixin
import pydash


class {python_class}Factory(PeerDBFactoryMixin, SQLModelFactory[{python_class}]):
    __random_seed__ = 0

    @classmethod
    def uint64(cls) -> int:
        return int(pydash.unique_id())
"""


class TestCreateModelCode(DatabaseTest):
    @pytest.fixture(scope="function")
    def clickhouse_table(
        self, clickhouse_adapter: ClickHouseAdapter
    ) -> Generator[ClickHouseTableIdentifier, Any, None]:
        clickhouse_adapter.create_table(table, create_table_statement)

        yield clickhouse_adapter.get_table(table)

        clickhouse_adapter.drop_table(table)

    def test_ok(self, clickhouse_adapter: ClickHouseAdapter, clickhouse_table: Table):
        result = create_model_code(clickhouse_adapter.settings, clickhouse_table.schema, dbt_source)

        assert result["model_code"].strip() == expected_model_code.strip()
        assert result["factory_code"].strip() == expected_factory_code.strip()
