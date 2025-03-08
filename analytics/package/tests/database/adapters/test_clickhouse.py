from clickhouse_connect.driver.exceptions import DatabaseError
from package.database import CHAdapter
from package.tests.asserts import assert_equal_ignoring_whitespace
from package.tests.fixtures.database import DBTest
from package.types import CHTableIdentifier
from sqlmodel import Session, Table, text
from typing import Any, Generator

import pytest


class TestCHAdapter(DBTest):
    @pytest.fixture(scope="function")
    def ch_table(self, ch_adapter: CHAdapter) -> Generator[CHTableIdentifier, Any, None]:
        table = "test_table"
        quoted_table = CHTableIdentifier(table=table).to_string()
        statement = f"""
        create or replace table {quoted_table}
        (
            id UInt64,
            updated_at DateTime default now()
        )
        engine = MergeTree
        order by id
        """

        ch_adapter.create_table(table, statement)

        yield ch_adapter.get_table(table)

        ch_adapter.drop_table(table)

    def test_create_client(self, ch_adapter: CHAdapter):
        with ch_adapter.create_client() as client:
            actual = client.query(
                "select 1 from system.databases where name = {database:String};",
                parameters={"database": ch_adapter.settings.database},
            ).result_rows
        assert actual == [(1,)]

    def test_create_session(self, ch_adapter: CHAdapter, ch_session: Session):
        actual = ch_session.exec(
            text("select 1 from system.databases where name = :database;").bindparams(
                database=ch_adapter.settings.database
            )
        ).all()
        assert actual == [(1,)]

    def test_has_database_non_existent(self, ch_adapter: CHAdapter):
        assert ch_adapter.has_database("non_existent") is False

    def test_has_database_existent(self, ch_adapter: CHAdapter):
        assert ch_adapter.has_database(ch_adapter.settings.database) is True

    def test_create_and_drop_database(self, ch_adapter: CHAdapter):
        database = "test_database"

        assert ch_adapter.has_database(database) is False

        ch_adapter.create_database(database)
        assert ch_adapter.has_database(database) is True

        ch_adapter.drop_database(database)
        assert ch_adapter.has_database(database) is False

    def test_has_table_non_existent(self, ch_adapter: CHAdapter):
        assert ch_adapter.has_table("non_existent") is False

    def test_has_table_existent(self, ch_adapter: CHAdapter, ch_table: Table):
        assert ch_adapter.has_table(ch_table.name) is True

    def test_get_table_non_existent(self, ch_adapter: CHAdapter):
        table = ch_adapter.get_table("non_existent")
        assert table is None

    def test_get_table_existent(self, ch_adapter: CHAdapter, ch_table: Table):
        table = ch_adapter.get_table(ch_table.name)
        assert set(["id", "updated_at"]) == set([column.name for column in table.columns])

    def test_create_and_drop_table(self, ch_adapter: CHAdapter):
        table = "test_table"
        quoted_table = CHTableIdentifier(table=table).to_string()
        statement = f"""
        create or replace table {quoted_table}
        (
            id UInt64,
            updated_at DateTime default now()
        )
        engine = MergeTree
        order by id
        """

        assert ch_adapter.has_table(table) is False

        ch_adapter.create_table(table, statement)
        assert ch_adapter.has_table(table) is True

        ch_adapter.drop_table(table)
        assert ch_adapter.has_table(table) is False

    def test_get_create_table_statement(self, ch_adapter: CHAdapter, ch_table: Table):
        with pytest.raises(DatabaseError):
            ch_adapter.get_create_table_statement("non_existent")

        expected = f"""
        CREATE TABLE {ch_adapter.settings.database}.{ch_table.name}
        (
            `id` UInt64,
            `updated_at` DateTime DEFAULT now()
        )
        ENGINE = MergeTree
        ORDER BY id
        SETTINGS index_granularity = 8192
        """
        assert_equal_ignoring_whitespace(
            ch_adapter.get_create_table_statement(ch_table.name), expected
        )

    def test_list_tables_empty_database(self, ch_adapter: CHAdapter):
        assert ch_adapter.list_tables() == []

    def test_list_tables_populated_database(self, ch_adapter: CHAdapter, ch_table: Table):
        assert set([ch_table.name]) == set([table.name for table in ch_adapter.list_tables()])

    def test_has_user_non_existent_user(self, ch_adapter: CHAdapter):
        assert ch_adapter.has_user("non_existent_user") is False

    def test_has_user_existent_user(self, ch_adapter: CHAdapter):
        assert ch_adapter.has_user(ch_adapter.settings.username) is True

    def test_create_and_drop_user(self, ch_adapter: CHAdapter):
        username = "test_user"
        password = "secret"

        assert ch_adapter.has_user(username) is False

        ch_adapter.create_user(username, password)
        assert ch_adapter.has_user(username) is True

        ch_adapter.drop_user(username)
        assert ch_adapter.has_user(username) is False
