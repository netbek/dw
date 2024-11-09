from .base import BaseAdapter
from collections.abc import Generator
from contextlib import contextmanager
from package.types import PGIdentifier, PGSettings, PGTableIdentifier
from sqlmodel import create_engine, MetaData, Table
from typing import Any, List, Optional

import psycopg2
import pydash


@contextmanager
def get_postgres_client(
    dsn: str, autocommit: bool = True
) -> Generator[tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor], Any, None]:
    connection = psycopg2.connect(dsn=dsn)
    try:
        connection.autocommit = autocommit
        with connection.cursor() as cursor:
            yield connection, cursor
    finally:
        connection.close()


class PGAdapter(BaseAdapter):
    def __init__(self, settings: PGSettings) -> None:
        super().__init__(settings)

    def get_client():
        raise NotImplementedError()

    def has_database(self, database: str) -> bool:
        statement = """
        select 1 from information_schema.schemata
        where catalog_name = %(database)s
        limit 1;
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"database": database})
            return bool(cur.fetchall())

    def create_database(self, database: str) -> None:
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

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"database": database, "schema": schema})
            return bool(cur.fetchall())

    def create_schema(self, schema: str, database: Optional[str] = None) -> None:
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

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"database": database, "schema": schema, "table": table})
            return bool(cur.fetchall())

    def create_table(
        self,
        table: str,
        statement: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        if self.has_table(table=table, database=database, schema=schema):
            return

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
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

        quoted_table = PGTableIdentifier(database=database, schema_=schema, table=table).to_string()
        statement = f"drop table {quoted_table};"

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def get_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> Table:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        url = self.settings.model_copy(update={"database": database}).to_url()
        engine = create_engine(url, echo=False)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine)

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

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"database": database, "schema": schema, "table": table})
            return cur.fetchone()[0]

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

        quoted_table = PGTableIdentifier(database=database, schema_=schema, table=table).to_string()
        statement = f"alter table {quoted_table} replica identity {replica_identity};"

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def list_tables(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Table]:
        if database is None:
            database = self.settings.database

        if schema is None:
            schema = self.settings.schema_

        url = self.settings.model_copy(update={"database": database}).to_url()
        engine = create_engine(url, echo=False)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine)

        return pydash.sort_by(list(metadata.tables.values()), lambda table: table.name)

    def has_user(self, username: str) -> bool:
        statement = """
        select 1
        from pg_catalog.pg_user
        where usename = %(username)s;
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"username": username})
            return bool(cur.fetchall())

    def create_user(self, username: str, password: str, options: Optional[dict] = None) -> None:
        if self.has_user(username):
            return

        quoted_username = PGIdentifier.quote(username)

        computed_options = []
        if options:
            if options.get("login"):
                computed_options.append("login")
            if options.get("replication"):
                computed_options.append("replication")

        statement = f"""
        create user {quoted_username}
        with {' '.join(computed_options)} password %(password)s;
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"password": password})

    def drop_user(self, username: str) -> None:
        if not self.has_user(username):
            return

        quoted_username = PGIdentifier.quote(username)
        statement = f"""
        drop owned by {quoted_username} cascade;
        drop user {quoted_username};
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def grant_user_privileges(self, username: str, schema: str) -> None:
        if not self.has_user(username):
            raise Exception()

        quoted_username = PGIdentifier.quote(username)
        quoted_schema = PGIdentifier.quote(schema)
        statement = f"""
        grant usage on schema {quoted_schema} to {quoted_username};
        grant select on all tables in schema {quoted_schema} to {quoted_username};
        alter default privileges in schema {quoted_schema} grant select on tables to {quoted_username};
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def revoke_user_privileges(self, username: str, schema: str) -> None:
        if not self.has_user(username):
            return

        quoted_username = PGIdentifier.quote(username)
        quoted_schema = PGIdentifier.quote(schema)
        statement = f"""
        alter default privileges for user {quoted_username} in schema {quoted_schema} revoke select on tables from {quoted_username};
        revoke select on all tables in schema {quoted_schema} from {quoted_username};
        revoke usage on schema {quoted_schema} from {quoted_username};
        -- reassign owned by {quoted_username} to postgres;
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
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

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"username": username})
            return cur.fetchall()

    def has_publication(self, publication: str) -> bool:
        statement = "select 1 from pg_publication where pubname = %(publication)s;"

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement, {"publication": publication})
            return bool(cur.fetchall())

    def create_publication(self, publication: str, tables: List[str], replace=False) -> None:
        if self.has_publication(publication):
            if replace:
                self.drop_publication(publication)
            else:
                raise Exception()

        quoted_publication = PGIdentifier.quote(publication)
        quoted_tables = [PGTableIdentifier.from_string(table).to_string() for table in tables]
        statement = f"create publication {quoted_publication} for table {", ".join(quoted_tables)};"

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def drop_publication(self, publication: str) -> None:
        if not self.has_publication(publication):
            return

        quoted_publication = PGIdentifier.quote(publication)
        statement = f"drop publication {quoted_publication};"

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)

    def list_publications(self) -> List[str]:
        statement = """
        select pubname as publication
        from pg_catalog.pg_publication;
        """

        with get_postgres_client(self.settings.to_url()) as (conn, cur):
            cur.execute(statement)
            return [row[0] for row in cur.fetchall()]
