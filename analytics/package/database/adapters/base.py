from abc import ABC, abstractmethod
from contextlib import contextmanager
from package.types import ClickHouseSettings, PostgresSettings
from sqlalchemy import URL
from sqlmodel import create_engine, Session, Table
from typing import Any, Generator, List, Optional, overload


class BaseAdapter(ABC):
    def __init__(self, settings: ClickHouseSettings | PostgresSettings) -> None:
        self.settings = settings

    @overload
    @classmethod
    @abstractmethod
    def create_url(
        cls,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        schema: str,
    ) -> URL: ...

    @overload
    @classmethod
    @abstractmethod
    def create_url(
        cls,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        driver: Optional[str] = None,
        secure: Optional[bool] = None,
    ) -> URL: ...

    @classmethod
    @abstractmethod
    def create_url(cls, *args, **kwargs) -> URL: ...

    @abstractmethod
    def create_client(): ...

    @contextmanager
    def create_engine(self):
        engine = create_engine(self.url, echo=False)

        yield engine

        engine.dispose()

    @contextmanager
    def create_session(self) -> Generator[Session, Any, None]:
        with self.create_engine() as engine:
            session = Session(engine)

        yield session

        session.close()

    @abstractmethod
    def has_database(self, database: str) -> bool: ...

    @abstractmethod
    def create_database(
        self, database: str, replace: Optional[bool] = False
    ) -> None: ...

    @abstractmethod
    def drop_database(self, database: str) -> None: ...

    @abstractmethod
    def has_schema(self, schema: str, database: Optional[str] = None) -> bool: ...

    @abstractmethod
    def create_schema(
        self,
        schema: str,
        database: Optional[str] = None,
        replace: Optional[bool] = False,
    ) -> None: ...

    @abstractmethod
    def drop_schema(self, schema: str, database: Optional[str] = None) -> None: ...

    @overload
    @abstractmethod
    def has_table(self, table: str, database: Optional[str] = None) -> bool: ...

    @overload
    @abstractmethod
    def has_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> bool: ...

    @abstractmethod
    def has_table(self, *args, **kwargs) -> bool: ...

    @overload
    @abstractmethod
    def create_table(
        self,
        table: str,
        statement: str,
        database: Optional[str] = None,
        replace: Optional[bool] = False,
    ) -> None: ...

    @overload
    @abstractmethod
    def create_table(
        self,
        table: str,
        statement: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        replace: Optional[bool] = False,
    ) -> None: ...

    @abstractmethod
    def create_table(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def get_create_table_statement(
        self, table: str, database: Optional[str] = None
    ) -> None: ...

    @overload
    @abstractmethod
    def get_create_table_statement(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def get_create_table_statement(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def drop_table(self, table: str, database: Optional[str] = None) -> None: ...

    @overload
    @abstractmethod
    def drop_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def drop_table(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def truncate_table(self, table: str, database: Optional[str] = None) -> None: ...

    @overload
    @abstractmethod
    def truncate_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def truncate_table(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def get_table(self, table: str, database: Optional[str] = None) -> Table: ...

    @overload
    @abstractmethod
    def get_table(
        self, table: str, database: Optional[str] = None, schema: Optional[str] = None
    ) -> Table: ...

    @abstractmethod
    def get_table(self, *args, **kwargs) -> Table: ...

    @overload
    @abstractmethod
    def get_table_replica_identity(
        self, table: str, database: Optional[str] = None
    ) -> None: ...

    @overload
    @abstractmethod
    def get_table_replica_identity(
        self,
        table: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None: ...

    @abstractmethod
    def get_table_replica_identity(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def set_table_replica_identity(
        self, table: str, replica_identity: str, database: Optional[str] = None
    ) -> None: ...

    @overload
    @abstractmethod
    def set_table_replica_identity(
        self,
        table: str,
        replica_identity: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> None: ...

    @abstractmethod
    def set_table_replica_identity(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def drop_tables(self, database: Optional[str] = None) -> None: ...

    @overload
    @abstractmethod
    def drop_tables(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> None: ...

    @abstractmethod
    def drop_tables(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def list_tables(self, database: Optional[str] = None) -> List[Table]: ...

    @overload
    @abstractmethod
    def list_tables(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Table]: ...

    @abstractmethod
    def list_tables(self, *args, **kwargs) -> List[Table]: ...

    @abstractmethod
    def has_user(self, username: str) -> bool: ...

    @overload
    @abstractmethod
    def create_user(
        self, username: str, password: str, replace: Optional[bool] = False
    ) -> None: ...

    @overload
    @abstractmethod
    def create_user(
        self,
        username: str,
        password: str,
        options: Optional[dict] = None,
        replace: Optional[bool] = False,
    ) -> None: ...

    @abstractmethod
    def create_user(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def drop_user(self, username: str) -> None: ...

    @overload
    @abstractmethod
    def grant_user_privileges(self, username: str, database: str) -> None: ...

    @overload
    @abstractmethod
    def grant_user_privileges(self, username: str, schema: str) -> None: ...

    @abstractmethod
    def grant_user_privileges(self, *args, **kwargs) -> None: ...

    @overload
    @abstractmethod
    def revoke_user_privileges(self, username: str, database: str) -> None: ...

    @overload
    @abstractmethod
    def revoke_user_privileges(self, username: str, schema: str) -> None: ...

    @abstractmethod
    def revoke_user_privileges(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def list_user_privileges(self, username: str) -> List[tuple]: ...

    @abstractmethod
    def has_publication(self, publication: str) -> bool: ...

    @abstractmethod
    def create_publication(self, publication: str, tables: List[str]) -> None: ...

    @abstractmethod
    def drop_publication(self, publication: str) -> None: ...

    @abstractmethod
    def list_publications(self) -> List[str]: ...
