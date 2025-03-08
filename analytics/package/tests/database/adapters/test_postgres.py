from package.database import PGAdapter
from package.tests.fixtures.database import DBTest
from package.types import PGTableIdentifier
from sqlmodel import Table, text
from typing import Any, Generator

import pytest


class TestPGAdapter(DBTest):
    @pytest.fixture(scope="function")
    def pg_user(self, pg_adapter: PGAdapter) -> Generator[str, Any, None]:
        username = "test_user"
        password = "secret"

        pg_adapter.create_user(username, password)

        yield username

        pg_adapter.drop_user(username)

    @pytest.fixture(scope="function")
    def pg_table(self, pg_adapter: PGAdapter) -> Generator[Table, Any, None]:
        table = "test_table"
        quoted_table = PGTableIdentifier(table=table).to_string()
        statement = f"""
        create table if not exists {quoted_table} (
            id bigint,
            updated_at timestamp default now()
        );
        """

        pg_adapter.create_table(table, statement)

        yield pg_adapter.get_table(table)

        pg_adapter.drop_table(table)

    @pytest.fixture(scope="function")
    def pg_publication(self, pg_adapter: PGAdapter, pg_table: Table) -> Generator[str, Any, None]:
        publication = "test_publication"

        pg_adapter.create_publication(publication, tables=[pg_table.name])

        yield publication

        pg_adapter.drop_publication(publication)

    def test_create_client(self, pg_adapter: PGAdapter):
        with pg_adapter.create_client() as (conn, cur):
            cur.execute(
                "select 1 from information_schema.schemata where catalog_name = %s limit 1;",
                [pg_adapter.settings.database],
            )
            actual = cur.fetchall()
        assert actual == [(1,)]

    def test_create_session(self, pg_adapter: PGAdapter):
        with pg_adapter.create_session() as session:
            actual = session.exec(
                text(
                    "select 1 from information_schema.schemata where catalog_name = :database limit 1;"
                ).bindparams(database=pg_adapter.settings.database)
            ).all()
        assert actual == [(1,)]

    def test_has_database_non_existent(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_database("non_existent") is False

    def test_has_database_existent(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_database(pg_adapter.settings.database) is True

    def test_has_schema_non_existent(self, pg_adapter: PGAdapter):
        tests = [
            ("non_existent", pg_adapter.settings.schema_),
            (pg_adapter.settings.database, "non_existent"),
            ("non_existent", "non_existent"),
        ]

        for database, schema in tests:
            assert pg_adapter.has_schema(schema, database=database) is False

    def test_has_schema_existent(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_schema(pg_adapter.settings.schema_) is True

    def test_has_table_non_existent(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_table("non_existent") is False

    def test_has_table_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        assert pg_adapter.has_table(pg_table.name) is True

    def test_get_table_non_existent(self, pg_adapter: PGAdapter):
        table = pg_adapter.get_table("non_existent")
        assert table is None

    def test_get_table_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        table = pg_adapter.get_table(pg_table.name)
        assert set(["id", "updated_at"]) == set([column.name for column in table.columns])

    def test_create_and_drop_table(self, pg_adapter: PGAdapter):
        table = "test_table"
        quoted_table = PGTableIdentifier(table=table).to_string()
        statement = f"""
        create table if not exists {quoted_table} (
            id bigint,
            updated_at timestamp default now()
        );
        """

        assert pg_adapter.has_table(table) is False

        pg_adapter.create_table(table, statement)
        assert pg_adapter.has_table(table) is True

        pg_adapter.drop_table(table)
        assert pg_adapter.has_table(table) is False

    def test_list_tables_empty_database(self, pg_adapter: PGAdapter):
        assert pg_adapter.list_tables() == []

    def test_list_tables_populated_database(self, pg_adapter: PGAdapter, pg_table: Table):
        assert set([pg_table.name]) == set([table.name for table in pg_adapter.list_tables()])

    def test_get_table_replica_identity_non_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        assert pg_adapter.get_table_replica_identity("non_existent_table") is None

    def test_get_table_replica_identity_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        assert pg_adapter.get_table_replica_identity(pg_table.name) == "default"

    def test_set_table_replica_identity_non_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        pg_adapter.set_table_replica_identity("non_existent_table", "full")

    def test_set_table_replica_identity_existent(self, pg_adapter: PGAdapter, pg_table: Table):
        assert pg_adapter.get_table_replica_identity(pg_table.name) == "default"
        pg_adapter.set_table_replica_identity(pg_table.name, "full")
        assert pg_adapter.get_table_replica_identity(pg_table.name) == "full"

    def test_has_user_non_existent_user(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_user("non_existent_user") is False

    def test_has_user_existent_user(self, pg_adapter: PGAdapter):
        assert pg_adapter.has_user(pg_adapter.settings.username) is True

    def test_create_and_drop_user(self, pg_adapter: PGAdapter):
        username = "test_user"
        password = "secret"

        assert pg_adapter.has_user(username) is False

        pg_adapter.create_user(username, password)
        assert pg_adapter.has_user(username) is True

        pg_adapter.drop_user(username)
        assert pg_adapter.has_user(username) is False

    def test_grant_and_revoke_user_privileges(
        self, pg_adapter: PGAdapter, pg_user: str, pg_table: Table
    ):
        pg_adapter.grant_user_privileges(pg_user, pg_adapter.settings.schema_)

        assert pg_adapter.list_user_privileges(pg_user) == [
            (pg_adapter.settings.database, pg_adapter.settings.schema_, pg_table.name, "SELECT")
        ]

        pg_adapter.revoke_user_privileges(pg_user, pg_adapter.settings.schema_)

        assert pg_adapter.list_user_privileges(pg_user) == []

    def test_create_and_drop_publication(self, pg_adapter: PGAdapter, pg_table: Table):
        publication = "test_publication"

        pg_adapter.create_publication(publication, [pg_table.name])
        assert pg_adapter.list_publications() == [publication]

        pg_adapter.drop_publication(publication)
        assert pg_adapter.list_publications() == []

    def test_list_publications(self, pg_adapter: PGAdapter, pg_publication: str):
        assert pg_adapter.list_publications() == [pg_publication]
