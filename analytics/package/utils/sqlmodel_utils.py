from package.database import ClickHouseAdapter
from package.types import ClickHouseSettings, DbtSource
from package.utils.python_utils import is_python_keyword
from typing import Dict, List, Optional

import datetime
import os
import pydash
import sqlglot
import sqlglot.expressions
import uuid

CLICKHOUSE_TYPES = [
    "AggregateFunction",
    "Array",
    "Boolean",
    "Date",
    "Date32",
    "DateTime",
    "DateTime64",
    "Decimal",
    "Enum",
    "Enum16",
    "Enum8",
    "Float",
    "Float32",
    "Float64",
    "IPv4",
    "IPv6",
    "Int",
    "Int128",
    "Int16",
    "Int256",
    "Int32",
    "Int64",
    "Int8",
    "LowCardinality",
    "Map",
    "Nested",
    "Nullable",
    "SimpleAggregateFunction",
    "String",
    "Tuple",
    "UInt128",
    "UInt16",
    "UInt256",
    "UInt32",
    "UInt64",
    "UInt8",
    "UUID",
]

SQLALCHEMY_TO_CLICKHOUSE_TYPE = {
    "Bool": "Boolean",
}

SQLGLOT_TO_PYTHON_TYPE = {
    sqlglot.expressions.DataType.Type.BIGINT: int,  # Int64
    sqlglot.expressions.DataType.Type.BOOLEAN: bool,  # Boolean
    sqlglot.expressions.DataType.Type.DATE32: datetime.date,  # Date32
    sqlglot.expressions.DataType.Type.DATETIME: datetime.datetime,  # DateTime
    sqlglot.expressions.DataType.Type.DATETIME64: datetime.datetime,  # DateTime64
    sqlglot.expressions.DataType.Type.DOUBLE: float,  # Float64
    sqlglot.expressions.DataType.Type.FLOAT: float,  # Float32
    sqlglot.expressions.DataType.Type.INT: int,  # Int32
    sqlglot.expressions.DataType.Type.SMALLINT: int,  # Int16
    sqlglot.expressions.DataType.Type.TEXT: str,  # String
    sqlglot.expressions.DataType.Type.TINYINT: int,  # Int8
    sqlglot.expressions.DataType.Type.UBIGINT: int,  # UInt64
    sqlglot.expressions.DataType.Type.UINT: int,  # UInt32
    sqlglot.expressions.DataType.Type.USMALLINT: int,  # UInt16
    sqlglot.expressions.DataType.Type.UTINYINT: int,  # UInt8
    sqlglot.expressions.DataType.Type.UUID: uuid.UUID,  # UUID
}

INDENT = pydash.repeat(" ", 4)


def parse_create_table_statement(statement: str) -> dict:
    result = {
        "engine": None,
        "version": None,
        "is_deleted": None,
        "primary_key": [],
        "order_by": [],
        "settings": {},
        "columns": [],
    }
    parsed = sqlglot.parse_one(statement, dialect="clickhouse")

    # Table engine
    node = parsed.find(sqlglot.exp.EngineProperty)

    if node:
        result["engine"] = node.this.name
        params = [param.name for param in node.this.iter_expressions()]

        if len(params) == 2:
            result["version"] = params[0]
            result["is_deleted"] = params[1]
        elif len(params) == 1:
            result["version"] = params[0]

    # Primary key
    node = parsed.find(sqlglot.exp.PrimaryKey)

    if node:
        result["primary_key"] = [expression.name for expression in node.iter_expressions()]

    # Order by
    node = parsed.find(sqlglot.exp.Ordered)

    if node:
        for expression in node.iter_expressions():
            for inner_expression in expression.iter_expressions():
                result["order_by"].append(inner_expression.name)

    # Settings
    node = parsed.find(sqlglot.exp.SettingsProperty)

    if node:
        for expression in node.iter_expressions():
            result["settings"][expression.this.name] = str(expression.expression)

    # Columns
    for node in parsed.find_all(sqlglot.exp.ColumnDef):
        name = node.name
        primary_key = name in result["primary_key"]
        nullable = node.kind.args.get("nullable")

        sqlglot_type = node.kind.args.get("this")
        python_type = SQLGLOT_TO_PYTHON_TYPE.get(sqlglot_type)
        sqlalchemy_type = to_sqlalchemy_type(node)

        if python_type is None:
            pydantic_type = "None"
        elif python_type.__module__ in ["datetime"]:
            pydantic_type = f"{python_type.__module__}.{python_type.__qualname__}"
            if nullable:
                pydantic_type = f"{pydantic_type} | None"
        else:
            pydantic_type = python_type.__qualname__
            if nullable:
                pydantic_type = f"{pydantic_type} | None"

        result["columns"].append(
            {
                "name": name,
                "primary_key": primary_key,
                "nullable": nullable,
                "sqlglot_type": sqlglot_type,
                "python_type": python_type,
                "pydantic_type": pydantic_type,
                "sqlalchemy_type": sqlalchemy_type,
            }
        )

    return result


def to_sqlalchemy_type(column_def: sqlglot.exp.ColumnDef) -> str:
    class ASTNode:
        pass

    class ArgumentNode(ASTNode):
        def __init__(self, value: str):
            self.value = value

        def __repr__(self):
            return self.value

    class SimpleTypeNode(ASTNode):
        def __init__(self, type_name: str):
            self.type_name = type_name

        def __repr__(self):
            return f"types.{self.type_name}"

    class NestedTypeNode(ASTNode):
        def __init__(self, modifier: str, inner: ASTNode):
            self.modifier = modifier
            self.inner = inner

        def __repr__(self):
            return f"types.{self.modifier}({self.inner})"

    def parse(string: str) -> ASTNode | None:
        if "(" in string and ")" in string:
            modifier, inner = string.split("(", 1)
            inner = inner.rsplit(")", 1)[0]  # Remove the outermost parentheses
            return NestedTypeNode(modifier.strip(), parse(inner.strip()))
        else:
            string = string.strip()

            if string in SQLALCHEMY_TO_CLICKHOUSE_TYPE:
                string = SQLALCHEMY_TO_CLICKHOUSE_TYPE[string]

            if string in CLICKHOUSE_TYPES:
                return SimpleTypeNode(string)
            else:
                return ArgumentNode(string)

    return parse(column_def.kind.sql(dialect="clickhouse"))


def serialize_dict(data: dict) -> str:
    return ", ".join(f"{key}={value}" for key, value in data.items())


def to_field_name(column_name: str) -> str:
    return column_name.lstrip("_")


def get_class_import_string(class_) -> str | None:
    if class_.__module__ == "builtins":
        return None
    elif class_.__module__ in ["datetime"]:
        return "import datetime"
    else:
        return f"from {class_.__module__} import {class_.__name__}"


def create_class_filename(class_name: str) -> str:
    filename = pydash.snake_case(class_name)

    # Fix keywords
    if is_python_keyword(filename):
        filename = filename + "_"

    return filename


def create_factory_name(model_name: str) -> str:
    return f"{model_name}Factory"


def create_model_code(
    db_settings: ClickHouseSettings,
    database: str,
    dbt_resource: DbtSource,
    extend_primary_key: Optional[bool] = False,
    random_seed: int = 0,
) -> Dict[str, str]:
    """Create the code of a SQLModel class from a table statement."""
    # 1. Create model
    clickhouse_adapter = ClickHouseAdapter(db_settings)
    table_name = dbt_resource.name
    model_name = dbt_resource.original_config.meta.python_class
    statement = clickhouse_adapter.get_create_table_statement(table_name, database=database)
    parsed_statement = parse_create_table_statement(statement)
    table_kwargs = {"schema": database}
    engine = parsed_statement["engine"]
    engine_kwargs = {}

    if parsed_statement["version"]:
        engine_kwargs["version"] = f"'{parsed_statement['version']}'"

    if parsed_statement["order_by"]:
        engine_kwargs["order_by"] = tuple(parsed_statement["order_by"])

    if parsed_statement["primary_key"]:
        engine_kwargs["primary_key"] = tuple(parsed_statement["primary_key"])

    if parsed_statement["settings"]:
        engine_kwargs.update(parsed_statement["settings"])

    imports = [
        "from clickhouse_sqlalchemy import engines",
        "from package.polyfactory.mixins import BaseMixin",
        "from package.sqlalchemy.clickhouse import types",
        "from sqlmodel import Column, Field, SQLModel",
    ]

    columns = []

    for column in parsed_statement["columns"]:
        dbt_column = pydash.find(
            dbt_resource.original_config.columns, lambda c: c.name == column["name"]
        )
        field_name = to_field_name(column["name"])

        if dbt_column and dbt_column.meta and dbt_column.meta.sqlalchemy_type:
            sqlalchemy_type = dbt_column.meta.sqlalchemy_type
        else:
            sqlalchemy_type = column["sqlalchemy_type"]

        sqlalchemy_column_kwargs = {
            "name": f"'{column['name']}'",
            "type_": sqlalchemy_type,
        }

        # ClickHouse does not require a unique primary key, but SQLAlchemy does. To work around
        # this, flag the _peerdb_version column as part of a composite primary key in SQLAlchemy.
        is_sqlalchemy_primary_key = column["primary_key"] or (
            extend_primary_key and column["name"] == "_peerdb_version"
        )

        if is_sqlalchemy_primary_key:
            sqlalchemy_column_kwargs["primary_key"] = True

        if not is_sqlalchemy_primary_key:
            sqlalchemy_column_kwargs["nullable"] = column["nullable"]

        field_kwargs = {
            "sa_column": f"Column({serialize_dict(sqlalchemy_column_kwargs)})",
        }

        column_def = (
            f"{field_name}: {column['pydantic_type']} = Field({serialize_dict(field_kwargs)})"
        )
        columns.append(column_def)

        class_import = get_class_import_string(column["python_type"])
        if class_import:
            imports.append(class_import)

    lines = []

    # Add table class
    lines.append(f"class {model_name}(BaseMixin, SQLModel, table=True):")
    lines.append(INDENT + f"__tablename__ = '{table_name}'")
    lines.append(
        INDENT
        + f"__table_args__ = (engines.{engine}({serialize_dict(engine_kwargs)}), {table_kwargs},)"
    )
    lines.append("")

    # Add columns
    for column in columns:
        lines.append(INDENT + column)

    # Add statement for reference, add imports
    imports = sorted(list(set(imports)))
    lines = ['"""\nCreated from:\n\n' + statement + '\n"""', ""] + imports + ["", ""] + lines

    model_code = "\n".join(lines) + "\n"

    # 2. Create factory
    model_filename = create_class_filename(model_name)
    factory_name = create_factory_name(model_name)

    imports = [
        f"from .{model_filename} import {model_name}",
        "from package.polyfactory.factories.sqlmodel_factory import SQLModelFactory",
        "from package.polyfactory.mixins import PeerDBFactoryMixin",
    ]

    lines = []

    # Add factory class
    lines.append(f"class {factory_name}(PeerDBFactoryMixin, SQLModelFactory[{model_name}]):")
    lines.append(INDENT + f"__random_seed__ = {random_seed}")

    for column in parsed_statement["columns"]:
        # If the column is an integer primary key, then generate a globally unique integer
        if column["python_type"] is int and column["primary_key"]:
            lines.append("")
            lines.append(INDENT + "@classmethod")
            lines.append(INDENT + f"def {column['name']}(cls) -> int:")
            lines.append(INDENT + INDENT + "return int(pydash.unique_id())")

            imports.append("import pydash")

    # Add imports
    imports = sorted(list(set(imports)))
    lines = imports + ["", ""] + lines

    factory_code = "\n".join(lines) + "\n"

    return {
        "model_code": model_code,
        "factory_code": factory_code,
    }


def create_model_file(
    db_settings: ClickHouseSettings,
    database: str,
    dbt_resource: DbtSource,
    directory: str,
    extend_primary_key: Optional[bool] = False,
    replace_model: Optional[bool] = False,
    replace_factory: Optional[bool] = False,
) -> None:
    model_name = dbt_resource.original_config.meta.python_class
    model_filename = create_class_filename(model_name)
    model_path = os.path.join(directory, f"{model_filename}.py")
    create_model = not os.path.exists(model_path) or replace_model

    factory_name = create_factory_name(model_name)
    factory_filename = create_class_filename(factory_name)
    factory_path = os.path.join(directory, f"{factory_filename}.py")
    create_factory = not os.path.exists(factory_path) or replace_factory

    if create_model or create_factory:
        result = create_model_code(
            db_settings, database, dbt_resource, extend_primary_key=extend_primary_key
        )

        if create_model:
            with open(model_path, "wt") as fp:
                fp.write(result["model_code"])

        if create_factory:
            with open(factory_path, "wt") as fp:
                fp.write(result["factory_code"])


def create_init_file(dbt_resources: List[DbtSource], directory: str) -> None:
    file_path = os.path.join(directory, "__init__.py")
    all = []
    imports = []

    for dbt_resource in dbt_resources:
        class_name = dbt_resource.original_config.meta.python_class

        model_filename = create_class_filename(class_name)
        all.append(class_name)
        imports.append(f"from .{model_filename} import {class_name}")

        factory_name = create_factory_name(class_name)
        factory_filename = create_class_filename(factory_name)
        all.append(factory_name)
        imports.append(f"from .{factory_filename} import {factory_name}")

    lines = [f"__all__ = {all}", "", "\n".join(imports), ""]
    code = "\n".join(lines)

    with open(file_path, "wt") as fp:
        fp.write(code)
