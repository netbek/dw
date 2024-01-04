from enum import Enum

import os

# Filesystem
HOME_DIR = os.environ["HOME"]
PROJECTS_DIR = os.path.join(HOME_DIR, "projects")
TEMPLATE_PROJECT_DIR = os.path.join(HOME_DIR, "template_project")

# dbt
DBT_PROFILES_DIR = os.environ["DBT_PROFILES_DIR"]
DBT_PROFILES_FILE = os.path.join(DBT_PROFILES_DIR, "profiles.yml")

# Prefect
PREFECT_HOME = os.environ["PREFECT_HOME"]
PREFECT_PROFILES_PATH = os.path.join(PREFECT_HOME, "profiles.toml")
PREFECT_PROVISION_PATH = os.path.join(PREFECT_HOME, "provision.yml")

"""
Map from dbt-codegen to ClickHouse data types that are case-sensitive.
See https://clickhouse.com/docs/en/operations/system-tables/data_type_families
Query:
    select '"' || lower(name) || '": "' || name || '",'
    from system.data_type_families
    where not case_insensitive
    order by name;
"""
CODEGEN_TO_CLICKHOUSE_DATA_TYPES = {
    "aggregatefunction": "AggregateFunction",
    "array": "Array",
    "enum16": "Enum16",
    "enum8": "Enum8",
    "fixedstring": "FixedString",
    "float32": "Float32",
    "float64": "Float64",
    "ipv4": "IPv4",
    "ipv6": "IPv6",
    "int128": "Int128",
    "int16": "Int16",
    "int256": "Int256",
    "int32": "Int32",
    "int64": "Int64",
    "int8": "Int8",
    "intervalday": "IntervalDay",
    "intervalhour": "IntervalHour",
    "intervalmicrosecond": "IntervalMicrosecond",
    "intervalmillisecond": "IntervalMillisecond",
    "intervalminute": "IntervalMinute",
    "intervalmonth": "IntervalMonth",
    "intervalnanosecond": "IntervalNanosecond",
    "intervalquarter": "IntervalQuarter",
    "intervalsecond": "IntervalSecond",
    "intervalweek": "IntervalWeek",
    "intervalyear": "IntervalYear",
    "lowcardinality": "LowCardinality",
    "map": "Map",
    "multipolygon": "MultiPolygon",
    "nested": "Nested",
    "nothing": "Nothing",
    "nullable": "Nullable",
    "object": "Object",
    "point": "Point",
    "polygon": "Polygon",
    "ring": "Ring",
    "simpleaggregatefunction": "SimpleAggregateFunction",
    "string": "String",
    "tuple": "Tuple",
    "uint128": "UInt128",
    "uint16": "UInt16",
    "uint256": "UInt256",
    "uint32": "UInt32",
    "uint64": "UInt64",
    "uint8": "UInt8",
    "uuid": "UUID",
}

# TODO Consolidate constants and enums
ACTION_CREATE = "create"
ACTION_DELETE = "delete"
ACTION_PAUSE = "pause"
ACTION_RESUME = "resume"


class DeploymentAction(str, Enum):
    delete = "delete"
    pause = "pause"
    resume = "resume"
