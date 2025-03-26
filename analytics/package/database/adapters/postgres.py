from collections.abc import Generator
from contextlib import contextmanager
from package.database.adapters.base import BaseAdapter
from package.types import PostgresIdentifier, PostgresSettings, PostgresTableIdentifier
from sqlalchemy import URL
from sqlmodel import create_engine, MetaData, Table
from typing import Any, List, Optional

import psycopg2
import pydash


class PostgresAdapter(BaseAdapter):
    def __init__(self, settings: PostgresSettings) -> None:
        super().__init__(settings)

    @classmethod
    def create_url(
        cls,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        schema: str,
    ) -> URL:
        return URL.create(
            "postgresql",
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    @property
    def url(self) -> URL:
        return self.create_url(
            self.settings.host,
            self.settings.port,
            self.settings.username,
            self.settings.password,
            self.settings.database,
            self.settings.schema_,
        )

    @contextmanager
    def create_client(
        self, autocommit: bool = True
    ) -> Generator[
        tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor], Any, None
    ]:
        connection = psycopg2.connect(
            host=self.settings.host,
            port=self.settings.port,
            user=self.settings.username,
            password=self.settings.password,
            database=self.settings.database,
        )

        connection.autocommit = autocommit

        with connection.cursor() as cursor:
            yield (connection, cursor)

        cursor.close()
        connection.close()

    def has_database(self, database: str) -> bool:
        statement = """
        select 1 from information_schema.schemata
        where catalog_name = %(database)s
        limit 1;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"database": database})
            result = bool(cur.fetchall())

        return result

    def create_database(self, database: str, replace: Optional[bool] = False) -> None:
        raise NotImplementedError()

    def drop_database(self, database: str) -> None:
        raise NotImplementedError()

    def has_schema(self, schema: str, database: Optional[str] = None):
        if database is None:
            database = self.settings.database

        statement = """
        select 1 from information_schema.schemata
        where catalog_name = %(database)s
        and schema_name = %(schema)s
        limit 1;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"database": database, "schema": schema})
            result = bool(cur.fetchall())

        return result

    def create_schema(
        self,
        schema: str,
        database: Optional[str] = None,
        replace: Optional[bool] = False,
    ) -> None:
        raise NotImplementedError()

    def drop_schema(self, schema: str, database: Optional[str] = None) -> None:
        raise NotImplementedError()

    def has_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> bool:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        statement = """
        select 1 from information_schema.tables
        where table_catalog = %(database)s
        and table_schema = %(schema)s
        and table_name = %(table)s;
        """

        with self.create_client() as (conn, cur):
            cur.execute(
                statement, {"database": database, "schema": schema, "table": table}
            )
            result = bool(cur.fetchall())

        return result

    def create_table(
        self,
        table: str,
        statement: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        replace: Optional[bool] = False,
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if self.has_table(table=table, database=database, schema=schema):
            if replace:
                self.drop_table(table=table, database=database, schema=schema)
            else:
                return

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def get_create_table_statement(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None:
        raise NotImplementedError()

    def drop_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if not self.has_table(table=table, database=database, schema=schema):
            return

        quoted_table = PostgresTableIdentifier(
            database=database, schema_=schema, table=table
        ).to_string()
        statement = f"drop table {quoted_table};"

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def truncate_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if not self.has_table(table=table, database=database, schema=schema):
            return

        quoted_table = PostgresTableIdentifier(
            database=database, schema_=schema, table=table
        ).to_string()
        statement = f"truncate table {quoted_table};"

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def get_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> Table:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        url = self.create_url(
            **self.settings.model_copy(update={"database": database}).model_dump(
                by_alias=True
            )
        )
        engine = create_engine(url, echo=False)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine, views=True)

        return metadata.tables.get(f"{schema}.{table}")

    def get_table_replica_identity(
        self,
        table: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if not self.has_table(table=table, database=database, schema=schema):
            return

        statement = """
        select
            case c.relreplident
                when 'd' then 'default'
                when 'n' then 'nothing'
                when 'f' then 'full'
                when 'i' then 'index'
            end as replica_identity
        from information_schema.tables as t
        join pg_class as c on c.oid = t.table_name::regclass
        where
            t.table_catalog = %(database)s
            and t.table_schema = %(schema)s
            and t.table_name = %(table)s;
        """

        with self.create_client() as (conn, cur):
            cur.execute(
                statement, {"database": database, "schema": schema, "table": table}
            )
            result = cur.fetchone()[0]

        return result

    def set_table_replica_identity(
        self,
        table: str,
        replica_identity: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if not self.has_table(table=table, database=database, schema=schema):
            return

        quoted_table = PostgresTableIdentifier(
            database=database, schema_=schema, table=table
        ).to_string()
        statement = f"alter table {quoted_table} replica identity {replica_identity};"

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def drop_tables(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        for table in self.list_tables(database=database, schema=schema):
            self.drop_table(table.name, database=database, schema=schema)

    def list_tables(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Table]:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        url = self.create_url(
            **self.settings.model_copy(update={"database": database}).model_dump(
                by_alias=True
            )
        )
        engine = create_engine(url, echo=False)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine, views=True)

        return pydash.sort_by(list(metadata.tables.values()), lambda table: table.name)

    def has_user(self, username: str) -> bool:
        statement = """
        select 1
        from pg_catalog.pg_user
        where usename = %(username)s;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"username": username})
            result = bool(cur.fetchall())

        return result

    def create_user(
        self,
        username: str,
        password: str,
        options: Optional[dict] = None,
        replace: Optional[bool] = False,
    ) -> None:
        if self.has_user(username):
            if replace:
                self.drop_user(username)
            else:
                return

        quoted_username = PostgresIdentifier.quote(username)

        computed_options = []
        if options:
            if options.get("login"):
                computed_options.append("login")
            if options.get("replication"):
                computed_options.append("replication")

        statement = f"""
        create user {quoted_username}
        with {" ".join(computed_options)} password %(password)s;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"password": password})

    def drop_user(self, username: str) -> None:
        if not self.has_user(username):
            return

        quoted_username = PostgresIdentifier.quote(username)
        statement = f"""
        drop owned by {quoted_username} cascade;
        drop user {quoted_username};
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def grant_user_privileges(self, username: str, schema: str) -> None:
        if not self.has_user(username):
            raise Exception()

        quoted_username = PostgresIdentifier.quote(username)
        quoted_schema = PostgresIdentifier.quote(schema)
        statement = f"""
        grant usage on schema {quoted_schema} to {quoted_username};
        grant select on all tables in schema {quoted_schema} to {quoted_username};
        alter default privileges in schema {quoted_schema} grant select on tables to {quoted_username};
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def revoke_user_privileges(self, username: str, schema: str) -> None:
        if not self.has_user(username):
            return

        quoted_username = PostgresIdentifier.quote(username)
        quoted_schema = PostgresIdentifier.quote(schema)
        statement = f"""
        alter default privileges for user {quoted_username} in schema {quoted_schema} revoke select on tables from {quoted_username};
        revoke select on all tables in schema {quoted_schema} from {quoted_username};
        revoke usage on schema {quoted_schema} from {quoted_username};
        -- reassign owned by {quoted_username} to postgres;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def list_user_privileges(self, username: str) -> List[tuple] | None:
        if not self.has_user(username):
            return

        statement = """
        select
            table_catalog as database,
            table_schema as schema,
            table_name as table,
            privilege_type as privilege
        from information_schema.role_table_grants
        where grantee = %(username)s
        order by 1, 2, 3, 4;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"username": username})
            result = cur.fetchall()

        return result

    def has_publication(self, publication: str) -> bool:
        statement = "select 1 from pg_publication where pubname = %(publication)s;"

        with self.create_client() as (conn, cur):
            cur.execute(statement, {"publication": publication})
            result = bool(cur.fetchall())

        return result

    def create_publication(
        self, publication: str, tables: List[str], replace=False
    ) -> None:
        if self.has_publication(publication):
            if replace:
                self.drop_publication(publication)
            else:
                raise Exception()

        quoted_publication = PostgresIdentifier.quote(publication)
        quoted_tables = [
            PostgresTableIdentifier.from_string(table).to_string() for table in tables
        ]
        statement = f"create publication {quoted_publication} for table {', '.join(quoted_tables)};"

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def drop_publication(self, publication: str) -> None:
        if not self.has_publication(publication):
            return

        quoted_publication = PostgresIdentifier.quote(publication)
        statement = f"drop publication {quoted_publication};"

        with self.create_client() as (conn, cur):
            cur.execute(statement)

    def list_publications(self) -> List[str]:
        statement = """
        select pubname as publication
        from pg_catalog.pg_publication;
        """

        with self.create_client() as (conn, cur):
            cur.execute(statement)
            result = [row[0] for row in cur.fetchall()]

        return result
