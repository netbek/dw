from clickhouse_connect.driver.exceptions import DatabaseError
from package.database import ClickHouseAdapter
from package.tests.asserts import assert_equal_ignoring_whitespace
from package.tests.fixtures.database import DatabaseTest
from package.types import ClickHouseTableIdentifier
from sqlmodel import Session, Table, text
from typing import Any, Generator

import pytest


class TestClickHouseAdapter(DatabaseTest):
    @pytest.fixture(scope="function")
    def clickhouse_table(
        self, clickhouse_adapter: ClickHouseAdapter
    ) -> Generator[ClickHouseTableIdentifier, Any, None]:
        table = "test_table"
        quoted_table = ClickHouseTableIdentifier(table=table).to_string()
        statement = f"""
        create or replace table {quoted_table}
        (
            id UInt64,
            updated_at DateTime default now()
        )
        engine = MergeTree
        order by id
        """

        clickhouse_adapter.create_table(table, statement)

        yield clickhouse_adapter.get_table(table)

        clickhouse_adapter.drop_table(table)

    def test_create_client(self, clickhouse_adapter: ClickHouseAdapter):
        with clickhouse_adapter.create_client() as client:
            actual = client.query(
                "select 1 from system.databases where name = {database:String};",
                parameters={"database": clickhouse_adapter.settings.database},
            ).result_rows
        assert actual == [(1,)]

    def test_create_session(
        self, clickhouse_adapter: ClickHouseAdapter, clickhouse_session: Session
    ):
        actual = clickhouse_session.exec(
            text("select 1 from system.databases where name = :database;").bindparams(
                database=clickhouse_adapter.settings.database
            )
        ).all()
        assert actual == [(1,)]

    def test_has_database_non_existent(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.has_database("non_existent") is False

    def test_has_database_existent(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.has_database(clickhouse_adapter.settings.database) is True

    def test_create_and_drop_database(self, clickhouse_adapter: ClickHouseAdapter):
        database = "test_database"

        assert clickhouse_adapter.has_database(database) is False

        clickhouse_adapter.create_database(database)
        assert clickhouse_adapter.has_database(database) is True

        clickhouse_adapter.drop_database(database)
        assert clickhouse_adapter.has_database(database) is False

    def test_has_table_non_existent(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.has_table("non_existent") is False

    def test_has_table_existent(
        self, clickhouse_adapter: ClickHouseAdapter, clickhouse_table: Table
    ):
        assert clickhouse_adapter.has_table(clickhouse_table.name) is True

    def test_get_table_non_existent(self, clickhouse_adapter: ClickHouseAdapter):
        table = clickhouse_adapter.get_table("non_existent")
        assert table is None

    def test_get_table_existent(
        self, clickhouse_adapter: ClickHouseAdapter, clickhouse_table: Table
    ):
        table = clickhouse_adapter.get_table(clickhouse_table.name)
        assert set(["id", "updated_at"]) == set([column.name for column in table.columns])

    def test_create_and_drop_table(self, clickhouse_adapter: ClickHouseAdapter):
        table = "test_table"
        quoted_table = ClickHouseTableIdentifier(table=table).to_string()
        statement = f"""
        create or replace table {quoted_table}
        (
            id UInt64,
            updated_at DateTime default now()
        )
        engine = MergeTree
        order by id
        """

        assert clickhouse_adapter.has_table(table) is False

        clickhouse_adapter.create_table(table, statement)
        assert clickhouse_adapter.has_table(table) is True

        clickhouse_adapter.drop_table(table)
        assert clickhouse_adapter.has_table(table) is False

    def test_get_create_table_statement(
        self, clickhouse_adapter: ClickHouseAdapter, clickhouse_table: Table
    ):
        with pytest.raises(DatabaseError):
            clickhouse_adapter.get_create_table_statement("non_existent")

        expected = f"""
        CREATE TABLE {clickhouse_adapter.settings.database}.{clickhouse_table.name}
        (
            `id` UInt64,
            `updated_at` DateTime DEFAULT now()
        )
        ENGINE = MergeTree
        ORDER BY id
        SETTINGS index_granularity = 8192
        """
        assert_equal_ignoring_whitespace(
            clickhouse_adapter.get_create_table_statement(clickhouse_table.name), expected
        )

    def test_list_tables_empty_database(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.list_tables() == []

    def test_list_tables_populated_database(
        self, clickhouse_adapter: ClickHouseAdapter, clickhouse_table: Table
    ):
        assert set([clickhouse_table.name]) == set(
            [table.name for table in clickhouse_adapter.list_tables()]
        )

    def test_has_user_non_existent_user(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.has_user("non_existent_user") is False

    def test_has_user_existent_user(self, clickhouse_adapter: ClickHouseAdapter):
        assert clickhouse_adapter.has_user(clickhouse_adapter.settings.username) is True

    def test_create_and_drop_user(self, clickhouse_adapter: ClickHouseAdapter):
        username = "test_user"
        password = "secret"

        assert clickhouse_adapter.has_user(username) is False

        clickhouse_adapter.create_user(username, password)
        assert clickhouse_adapter.has_user(username) is True

        clickhouse_adapter.drop_user(username)
        assert clickhouse_adapter.has_user(username) is False
