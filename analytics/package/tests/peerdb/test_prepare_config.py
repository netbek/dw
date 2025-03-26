from package.config.settings import get_settings
from package.database import PostgresAdapter
from package.peerdb import PeerDB
from package.tests.fixtures.database import DatabaseTest
from package.types import DbtSource
from sqlmodel import Table
from typing import Any, Generator, List

import pytest
import yaml

settings = get_settings()

table_defs = [
    (
        "table_1",
        """
        create table table_1 (
            id bigint,
            username text,
            password text,
            age smallint,
            modified_at timestamp(6)
        );
        """,
    ),
    (
        "table_2",
        """
        create table table_2 (
            id bigint,
            longitude double precision,
            latitude double precision,
            is_secret boolean,
            modified_at timestamp(6)
        );
        """,
    ),
    (
        "table_3",
        """
        create table table_3 (
            id bigint,
            ts timestamp(6),
            modified_at timestamp(6)
        );
        """,
    ),
]

peerdb_yaml = f"""
peers:
  source:
    type: 3
    postgres_config:
      host: {settings.test_postgres.host}
      port: {settings.test_postgres.port}
      user: {settings.test_postgres.username}
      password: {settings.test_postgres.password}
      database: {settings.test_postgres.database}

  destination:
    type: 8
    clickhouse_config:
      host: {settings.test_clickhouse.host}
      http_port: {settings.test_clickhouse.http_port}
      tcp_port: {settings.test_clickhouse.tcp_port}
      user: {settings.test_clickhouse.username}
      password: {settings.test_clickhouse.password}
      database: {settings.test_clickhouse.database}

mirrors:
  +do_initial_snapshot: false
  +resync: false

  cdc_small:
    source_name: source
    destination_name: destination
    table_mappings:
    - source_table_identifier: public.table_1
      destination_table_identifier: table_1
    resync: true

  cdc_large:
    source_name: source
    destination_name: destination
    table_mappings:
    - source_table_identifier: public.table_2
      destination_table_identifier: table_2
    - source_table_identifier: public.table_3
      destination_table_identifier: table_3

publications:
  publication_1:
  - private.table_1
  - private.table_2
  publication_2:
  - private.table_3
"""

list_resources__return_value = [
    {
        "name": "table_1",
        "resource_type": "source",
        "package_name": "test",
        "original_file_path": "models/sources.yml",
        "unique_id": "source.test.default.table_1",
        "source_name": settings.test_clickhouse.database,
        "tags": [],
        "config": {"enabled": True},
        "original_config": {
            "name": "table_1",
            "columns": [
                {"name": "id", "data_type": "Int64"},
                {"name": "username", "data_type": "String"},
                {"name": "_peerdb_is_deleted", "data_type": "Int8"},
                {"name": "_peerdb_synced_at", "data_type": "DateTime64(9)"},
                {"name": "_peerdb_version", "data_type": "Int64"},
            ],
        },
    },
    {
        "name": "table_2",
        "resource_type": "source",
        "package_name": "test",
        "original_file_path": "models/sources.yml",
        "unique_id": "source.test.default.table_2",
        "source_name": settings.test_clickhouse.database,
        "tags": [],
        "config": {"enabled": True},
        "original_config": {
            "name": "table_2",
            "columns": [
                {"name": "id", "data_type": "Int64"},
                {"name": "longitude", "data_type": "Float64"},
                {"name": "latitude", "data_type": "Float64"},
                {"name": "_peerdb_is_deleted", "data_type": "Int8"},
                {"name": "_peerdb_synced_at", "data_type": "DateTime64(9)"},
                {"name": "_peerdb_version", "data_type": "Int64"},
            ],
        },
    },
    {
        "name": "table_3",
        "resource_type": "source",
        "package_name": "test",
        "original_file_path": "models/sources.yml",
        "unique_id": "source.test.default.table_3",
        "source_name": settings.test_clickhouse.database,
        "tags": [],
        "config": {"enabled": True},
        "original_config": {
            "name": "table_3",
            "columns": [
                {"name": "id", "data_type": "Int64"},
                {"name": "ts", "data_type": "DateTime64(6)"},
                {"name": "_peerdb_is_deleted", "data_type": "Int8"},
                {"name": "_peerdb_synced_at", "data_type": "DateTime64(9)"},
                {"name": "_peerdb_version", "data_type": "Int64"},
            ],
        },
    },
]
list_resources__return_value = [DbtSource(**source) for source in list_resources__return_value]


class TestEmptyPeerDBConfig(DatabaseTest):
    @pytest.fixture(scope="function")
    def postgres_tables(
        self, postgres_adapter: PostgresAdapter
    ) -> Generator[List[Table], Any, None]:
        for table_def in table_defs:
            postgres_adapter.create_table(*table_def)

        table_names = [table_def[0] for table_def in table_defs]
        tables = [table for table in postgres_adapter.list_tables() if table.name in table_names]

        yield tables

        for table_name in table_names:
            postgres_adapter.drop_table(table_name)

    def test_func(self, postgres_tables: List[Table]):
        peerdb_config = {}
        actual = PeerDB.prepare_config(peerdb_config, dbt_project_dir="/", generate_exclude=True)
        expected = {
            "mirrors": {},
            "peers": {},
            "publication_schemas": [],
            "publications": {},
            "users": {},
        }

        assert actual == expected


class TestSourcePeerMissingTable(DatabaseTest):
    @pytest.fixture(scope="function")
    def postgres_tables(
        self, postgres_adapter: PostgresAdapter
    ) -> Generator[List[Table], Any, None]:
        for table_def in table_defs[:1]:
            postgres_adapter.create_table(*table_def)

        table_names = [table_def[0] for table_def in table_defs[:1]]
        tables = [table for table in postgres_adapter.list_tables() if table.name in table_names]

        yield tables

        for table_name in table_names:
            postgres_adapter.drop_table(table_name)

    @pytest.fixture(scope="function")
    def list_resources(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "package.peerdb.Dbt.list_resources",
            lambda *args, **kwargs: list_resources__return_value,
        )

    def test_func(self, postgres_tables: List[Table], list_resources: None):
        peerdb_config = yaml.safe_load(peerdb_yaml)

        with pytest.raises(Exception) as exc:
            PeerDB.prepare_config(peerdb_config, dbt_project_dir="/", generate_exclude=True)

        assert (
            str(exc.value) == "Source table 'public.table_2' not found in database of peer 'source'"
        )


class TestDbtMissingTable(DatabaseTest):
    @pytest.fixture(scope="function")
    def postgres_tables(
        self, postgres_adapter: PostgresAdapter
    ) -> Generator[List[Table], Any, None]:
        for table_def in table_defs:
            postgres_adapter.create_table(*table_def)

        table_names = [table_def[0] for table_def in table_defs]
        tables = [table for table in postgres_adapter.list_tables() if table.name in table_names]

        yield tables

        for table_name in table_names:
            postgres_adapter.drop_table(table_name)

    @pytest.fixture(scope="function")
    def list_resources(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "package.peerdb.Dbt.list_resources",
            lambda *args, **kwargs: list_resources__return_value[:1],
        )

    def test_func(self, postgres_tables: List[Table], list_resources: None):
        peerdb_config = yaml.safe_load(peerdb_yaml)

        with pytest.raises(Exception) as exc:
            PeerDB.prepare_config(peerdb_config, dbt_project_dir="/", generate_exclude=True)

        assert str(exc.value) == "Destination table 'table_2' not found in dbt config"


class TestOK(DatabaseTest):
    @pytest.fixture(scope="function")
    def postgres_tables(
        self, postgres_adapter: PostgresAdapter
    ) -> Generator[List[Table], Any, None]:
        for table_def in table_defs:
            postgres_adapter.create_table(*table_def)

        table_names = [table_def[0] for table_def in table_defs]
        tables = [table for table in postgres_adapter.list_tables() if table.name in table_names]

        yield tables

        for table_name in table_names:
            postgres_adapter.drop_table(table_name)

    @pytest.fixture(scope="function")
    def list_resources(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "package.peerdb.Dbt.list_resources",
            lambda *args, **kwargs: list_resources__return_value,
        )

    def test_func(self, postgres_tables: List[Table], list_resources: None):
        peerdb_config = yaml.safe_load(peerdb_yaml)
        actual = PeerDB.prepare_config(peerdb_config, dbt_project_dir="/", generate_exclude=True)
        expected = {
            "mirrors": {
                "cdc_small": {
                    "source_name": "source",
                    "destination_name": "destination",
                    "table_mappings": [
                        {
                            "source_table_identifier": "public.table_1",
                            "destination_table_identifier": "table_1",
                            "exclude": ["age", "modified_at", "password"],
                        }
                    ],
                    "do_initial_snapshot": False,
                    "resync": True,
                    "flow_job_name": "cdc_small",
                },
                "cdc_large": {
                    "source_name": "source",
                    "destination_name": "destination",
                    "table_mappings": [
                        {
                            "source_table_identifier": "public.table_2",
                            "destination_table_identifier": "table_2",
                            "exclude": ["is_secret", "modified_at"],
                        },
                        {
                            "source_table_identifier": "public.table_3",
                            "destination_table_identifier": "table_3",
                            "exclude": ["modified_at"],
                        },
                    ],
                    "do_initial_snapshot": False,
                    "resync": False,
                    "flow_job_name": "cdc_large",
                },
            },
            "peers": {
                "source": {
                    "type": 3,
                    "postgres_config": {
                        "host": settings.test_postgres.host,
                        "port": settings.test_postgres.port,
                        "user": settings.test_postgres.username,
                        "password": settings.test_postgres.password,
                        "database": settings.test_postgres.database,
                    },
                    "name": "source",
                },
                "destination": {
                    "type": 8,
                    "clickhouse_config": {
                        "host": settings.test_clickhouse.host,
                        "http_port": settings.test_clickhouse.http_port,
                        "tcp_port": settings.test_clickhouse.tcp_port,
                        "user": settings.test_clickhouse.username,
                        "password": settings.test_clickhouse.password,
                        "database": settings.test_clickhouse.database,
                    },
                    "name": "destination",
                },
            },
            "publication_schemas": ["private", "public"],
            "publications": {
                "publication_1": {
                    "name": "publication_1",
                    "table_identifiers": [
                        "private.table_1",
                        "private.table_2",
                    ],
                },
                "publication_2": {
                    "name": "publication_2",
                    "table_identifiers": [
                        "private.table_3",
                    ],
                },
            },
            "users": {},
        }

        assert actual == expected
