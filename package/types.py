from pydantic import BaseModel
from typing import List, Literal, Optional


class DBSettings(BaseModel):
    type: Literal["clickhouse", "postgresql"]
    driver: Optional[str] = None
    host: str
    port: str
    username: str
    password: str
    database: str


class CHIdentifier(BaseModel):
    @classmethod
    def quote(cls, identifier: str) -> str:
        return f"`{identifier}`"

    @classmethod
    def unquote(cls, identifier: str) -> str:
        return identifier.strip("`")


class CHTableIdentifier(CHIdentifier):
    database: Optional[str] = None
    table: str

    @classmethod
    def from_string(cls, identifier: str) -> "CHTableIdentifier":
        parts = [CHIdentifier.unquote(identifier) for part in identifier.split(".")]

        if len(parts) == 2:
            return cls(database=parts[0], table=parts[1])
        elif len(parts) == 1:
            return cls(table=parts[0])
        else:
            raise ValueError()

    def to_string(self) -> str:
        if self.database is None:
            return CHIdentifier.quote(self.table)
        else:
            return f"{CHIdentifier.quote(self.database)}.{CHIdentifier.quote(self.table)}"


class PGIdentifier(BaseModel):
    @classmethod
    def quote(cls, identifier: str) -> str:
        return f'"{identifier}"'

    @classmethod
    def unquote(cls, identifier: str) -> str:
        return identifier.strip('"')


class PGTableIdentifier(PGIdentifier):
    schema_: Optional[str] = None
    table: str

    @classmethod
    def from_string(cls, identifier: str) -> "PGTableIdentifier":
        parts = [PGIdentifier.unquote(identifier) for part in identifier.split(".")]

        if len(parts) == 2:
            return cls(schema_=parts[0], table=parts[1])
        elif len(parts) == 1:
            return cls(table=parts[0])
        else:
            raise ValueError()

    def to_string(self) -> str:
        if self.schema_ is None:
            return PGIdentifier.quote(self.table)
        else:
            return f"{PGIdentifier.quote(self.schema_)}.{PGIdentifier.quote(self.table)}"


class DbtColumnMeta(BaseModel):
    sqlalchemy_type: str


class DbtColumn(BaseModel):
    name: str
    data_type: str
    meta: Optional[DbtColumnMeta] = None


class DbtSourceTableMeta(BaseModel):
    class_name: str


class DbtSourceTable(BaseModel):
    name: str
    columns: Optional[List[DbtColumn]] = None
    meta: Optional[DbtSourceTableMeta] = None


class DbtSource(BaseModel):
    name: str
    tables: List[DbtSourceTable]


class DbtSourcesConfig(BaseModel):
    version: int
    sources: List[DbtSource]

    def get_sources_by_name(self, *names: str) -> List[DbtSource]:
        return [source for source in self.sources if source.name in names]
