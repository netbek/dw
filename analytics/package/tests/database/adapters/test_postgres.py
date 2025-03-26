from package.database import PostgresAdapter
from package.tests.fixtures.database import DatabaseTest
from package.types import PostgresTableIdentifier
from sqlmodel import Table, text
from typing import Any, Generator

import pytest


class TestPostgresAdapter(DatabaseTest):
    @pytest.fixture(scope="function")
    def postgres_user(self, postgres_adapter: PostgresAdapter) -> Generator[str, Any, None]:
        username = "test_user"
        password = "secret"

        postgres_adapter.create_user(username, password)

        yield username

        postgres_adapter.drop_user(username)

    @pytest.fixture(scope="function")
    def postgres_table(self, postgres_adapter: PostgresAdapter) -> Generator[Table, Any, None]:
        table = "test_table"
        quoted_table = PostgresTableIdentifier(table=table).to_string()
        statement = f"""
        create table if not exists {quoted_table} (
            id bigint,
            updated_at timestamp default now()
        );
        """

        postgres_adapter.create_table(table, statement)

        yield postgres_adapter.get_table(table)

        postgres_adapter.drop_table(table)

    @pytest.fixture(scope="function")
    def postgres_publication(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ) -> Generator[str, Any, None]:
        publication = "test_publication"

        postgres_adapter.create_publication(publication, tables=[postgres_table.name])

        yield publication

        postgres_adapter.drop_publication(publication)

    def test_create_client(self, postgres_adapter: PostgresAdapter):
        with postgres_adapter.create_client() as (conn, cur):
            cur.execute(
                "select 1 from information_schema.schemata where catalog_name = %s limit 1;",
                [postgres_adapter.settings.database],
            )
            actual = cur.fetchall()
        assert actual == [(1,)]

    def test_create_session(self, postgres_adapter: PostgresAdapter):
        with postgres_adapter.create_session() as session:
            actual = session.exec(
                text(
                    "select 1 from information_schema.schemata where catalog_name = :database limit 1;"
                ).bindparams(database=postgres_adapter.settings.database)
            ).all()
        assert actual == [(1,)]

    def test_has_database_non_existent(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_database("non_existent") is False

    def test_has_database_existent(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_database(postgres_adapter.settings.database) is True

    def test_has_schema_non_existent(self, postgres_adapter: PostgresAdapter):
        tests = [
            ("non_existent", postgres_adapter.settings.schema_),
            (postgres_adapter.settings.database, "non_existent"),
            ("non_existent", "non_existent"),
        ]

        for database, schema in tests:
            assert postgres_adapter.has_schema(schema, database=database) is False

    def test_has_schema_existent(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_schema(postgres_adapter.settings.schema_) is True

    def test_has_table_non_existent(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_table("non_existent") is False

    def test_has_table_existent(self, postgres_adapter: PostgresAdapter, postgres_table: Table):
        assert postgres_adapter.has_table(postgres_table.name) is True

    def test_get_table_non_existent(self, postgres_adapter: PostgresAdapter):
        table = postgres_adapter.get_table("non_existent")
        assert table is None

    def test_get_table_existent(self, postgres_adapter: PostgresAdapter, postgres_table: Table):
        table = postgres_adapter.get_table(postgres_table.name)
        assert set(["id", "updated_at"]) == set([column.name for column in table.columns])

    def test_create_and_drop_table(self, postgres_adapter: PostgresAdapter):
        table = "test_table"
        quoted_table = PostgresTableIdentifier(table=table).to_string()
        statement = f"""
        create table if not exists {quoted_table} (
            id bigint,
            updated_at timestamp default now()
        );
        """

        assert postgres_adapter.has_table(table) is False

        postgres_adapter.create_table(table, statement)
        assert postgres_adapter.has_table(table) is True

        postgres_adapter.drop_table(table)
        assert postgres_adapter.has_table(table) is False

    def test_list_tables_empty_database(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.list_tables() == []

    def test_list_tables_populated_database(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        assert set([postgres_table.name]) == set(
            [table.name for table in postgres_adapter.list_tables()]
        )

    def test_get_table_replica_identity_non_existent(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        assert postgres_adapter.get_table_replica_identity("non_existent_table") is None

    def test_get_table_replica_identity_existent(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        assert postgres_adapter.get_table_replica_identity(postgres_table.name) == "default"

    def test_set_table_replica_identity_non_existent(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        postgres_adapter.set_table_replica_identity("non_existent_table", "full")

    def test_set_table_replica_identity_existent(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        assert postgres_adapter.get_table_replica_identity(postgres_table.name) == "default"
        postgres_adapter.set_table_replica_identity(postgres_table.name, "full")
        assert postgres_adapter.get_table_replica_identity(postgres_table.name) == "full"

    def test_has_user_non_existent_user(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_user("non_existent_user") is False

    def test_has_user_existent_user(self, postgres_adapter: PostgresAdapter):
        assert postgres_adapter.has_user(postgres_adapter.settings.username) is True

    def test_create_and_drop_user(self, postgres_adapter: PostgresAdapter):
        username = "test_user"
        password = "secret"

        assert postgres_adapter.has_user(username) is False

        postgres_adapter.create_user(username, password)
        assert postgres_adapter.has_user(username) is True

        postgres_adapter.drop_user(username)
        assert postgres_adapter.has_user(username) is False

    def test_grant_and_revoke_user_privileges(
        self, postgres_adapter: PostgresAdapter, postgres_user: str, postgres_table: Table
    ):
        postgres_adapter.grant_user_privileges(postgres_user, postgres_adapter.settings.schema_)

        assert postgres_adapter.list_user_privileges(postgres_user) == [
            (
                postgres_adapter.settings.database,
                postgres_adapter.settings.schema_,
                postgres_table.name,
                "SELECT",
            )
        ]

        postgres_adapter.revoke_user_privileges(postgres_user, postgres_adapter.settings.schema_)

        assert postgres_adapter.list_user_privileges(postgres_user) == []

    def test_create_and_drop_publication(
        self, postgres_adapter: PostgresAdapter, postgres_table: Table
    ):
        publication = "test_publication"

        postgres_adapter.create_publication(publication, [postgres_table.name])
        assert postgres_adapter.list_publications() == [publication]

        postgres_adapter.drop_publication(publication)
        assert postgres_adapter.list_publications() == []

    def test_list_publications(self, postgres_adapter: PostgresAdapter, postgres_publication: str):
        assert postgres_adapter.list_publications() == [postgres_publication]
