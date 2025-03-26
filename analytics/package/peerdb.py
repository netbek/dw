from package.config.constants import PEERDB_SOURCE_PEER
from package.database import ClickHouseAdapter, PostgresAdapter
from package.dbt import Dbt
from package.types import (
    ClickHouseSettings,
    ClickHouseTableIdentifier,
    DbtResourceType,
    PostgresSettings,
    PostgresTableIdentifier,
)
from pathlib import Path
from typing import Optional

import copy
import httpx
import pydash


def to_clickhouse_settings(clickhouse_config: dict) -> ClickHouseSettings:
    return ClickHouseSettings(
        host=clickhouse_config["host"],
        port=clickhouse_config["port"],
        username=clickhouse_config["user"],
        password=clickhouse_config["password"],
        database=clickhouse_config["database"],
        driver="native",
        secure=not clickhouse_config.get("disable_tls", False),
    )


def to_postgres_settings(postgres_config: dict) -> PostgresSettings:
    return PostgresSettings(
        host=postgres_config["host"],
        port=postgres_config["port"],
        username=postgres_config["user"],
        password=postgres_config["password"],
        database=postgres_config["database"],
        schema_="public",
    )


class MirrorNotFound(Exception):
    pass


class PeerDB:
    def __init__(self, api_url: str) -> None:
        self._api_url = api_url
        self._headers = {"Content-Type": "application/json"}

    @classmethod
    def prepare_config(
        cls,
        config: dict,
        dbt_project_dir: Optional[Path | str] = None,
        generate_exclude: Optional[bool] = False,
    ) -> dict:
        def process_node(node: dict) -> dict:
            default_keys = [key for key in node.keys() if key.startswith("+")]
            defaults = {key.lstrip("+").strip(): node[key] for key in default_keys}

            if defaults:
                for key in node.keys():
                    if not key.startswith("+"):
                        node[key] = pydash.defaults(node[key], defaults)

                node = pydash.omit(node, *default_keys)

            return node

        result = copy.deepcopy(config)

        if "users" not in result:
            result["users"] = {}

        if "publications" in result:
            for key, value in result["publications"].items():
                result["publications"][key] = {
                    "name": key,
                    "table_identifiers": value,
                }
        else:
            result["publications"] = {}

        if "peers" in result:
            result["peers"] = process_node(result["peers"])

            for key, value in result["peers"].items():
                result["peers"][key]["name"] = key
        else:
            result["peers"] = {}

        if "mirrors" in result:
            result["mirrors"] = process_node(result["mirrors"])

            for key, value in result["mirrors"].items():
                result["mirrors"][key]["flow_job_name"] = key

            if generate_exclude and result["mirrors"]:
                if dbt_project_dir is None:
                    raise Exception("'dbt_project_dir' is required")

                source_peer = result["peers"].get(PEERDB_SOURCE_PEER)

                if not source_peer:
                    raise Exception(
                        f"Peer '{PEERDB_SOURCE_PEER}' not found in PeerDB config"
                    )

                postgres_settings = to_postgres_settings(source_peer["postgres_config"])
                source_adapter = PostgresAdapter(postgres_settings)
                source_tables = source_adapter.list_tables()

                dbt = Dbt(dbt_project_dir)
                dbt_sources = dbt.list_resources(
                    resource_types=[DbtResourceType.SOURCE]
                )

                # Validate the table mappings and compute the excluded columns
                for mirror in result["mirrors"].values():
                    computed_table_mappings = []

                    for table_mapping in mirror["table_mappings"]:
                        # Find the source table in the source database
                        source_table_identifier = PostgresTableIdentifier.from_string(
                            table_mapping["source_table_identifier"]
                        )
                        source_table = pydash.find(
                            source_tables,
                            lambda table: (
                                table.schema == source_table_identifier.schema_
                                and table.name == source_table_identifier.table
                            ),
                        )

                        if source_table is None:
                            raise Exception(
                                f"Source table '{table_mapping['source_table_identifier']}' not found in database of peer '{PEERDB_SOURCE_PEER}'"
                            )

                        # Find the destination table in the dbt sources config
                        destination_table_identifier = (
                            ClickHouseTableIdentifier.from_string(
                                table_mapping["destination_table_identifier"]
                            )
                        )
                        dbt_source = pydash.find(
                            dbt_sources,
                            lambda source: source.name
                            == destination_table_identifier.table,
                        )

                        if dbt_source is None:
                            raise Exception(
                                f"Destination table '{table_mapping['destination_table_identifier']}' not found in dbt config"
                            )

                        # Compute the excluded columns (difference between source and destination tables)
                        source_columns = [
                            str(column.name) for column in source_table.columns
                        ]
                        dbt_source_columns = [
                            column.name for column in dbt_source.original_config.columns
                        ]
                        computed_exclude = pydash.difference(
                            source_columns, dbt_source_columns
                        )
                        computed_exclude = sorted(computed_exclude)

                        # Compute the table mapping
                        computed_table_mapping = pydash.assign(
                            pydash.pick(
                                table_mapping,
                                [
                                    "source_table_identifier",
                                    "destination_table_identifier",
                                ],
                            ),
                            {"exclude": computed_exclude},
                        )
                        computed_table_mappings.append(computed_table_mapping)

                    mirror["table_mappings"] = computed_table_mappings
        else:
            result["mirrors"] = {}

        publication_schemas = []

        for value in result["publications"].values():
            for identifier in value["table_identifiers"]:
                source_table_identifier = PostgresTableIdentifier.from_string(
                    identifier
                )
                publication_schemas.append(source_table_identifier.schema_)

        for value in result["mirrors"].values():
            for table_mapping in value["table_mappings"]:
                source_table_identifier = PostgresTableIdentifier.from_string(
                    table_mapping["source_table_identifier"]
                )
                publication_schemas.append(source_table_identifier.schema_)

        result["publication_schemas"] = sorted(pydash.uniq(publication_schemas))

        return result

    def update_settings(self, settings: dict) -> None:
        url = f"{self._api_url}/v1/dynamic_settings"

        for key, value in settings.items():
            data = {"name": key, "value": value}
            response = httpx.post(url, json=data, headers=self._headers)

            if response.status_code != 200:
                raise Exception(
                    f"Failed to set {key}={value} (error {response.status_code}: {response.text})"
                )

    def has_peer(self, peer: dict) -> bool:
        url = f"{self._api_url}/v1/peers/list"
        response = httpx.get(url, headers=self._headers)
        items = response.json().get("items", [])
        matched_items = [item for item in items if item["name"] == peer["name"]]

        return bool(matched_items)

    def create_peer(self, peer: dict) -> None:
        if not self.has_peer(peer):
            url = f"{self._api_url}/v1/peers/create"
            data = {"peer": peer}
            response = httpx.post(url, json=data, headers=self._headers)
            status = response.json().get("status")

            if not (response.status_code == 200 and status == "CREATED"):
                raise Exception(
                    f"Failed to create peer '{peer['name']}' (error {response.status_code}: {response.text})"
                )

    def drop_peer(self, peer: dict) -> None:
        if self.has_peer(peer):
            url = f"{self._api_url}/v1/peers/drop"
            data = {"peerName": peer["name"]}
            response = httpx.post(url, json=data, headers=self._headers, timeout=None)

            if not (response.status_code == 200):
                raise Exception(
                    f"Failed to drop peer '{peer['name']}' (error {response.status_code}: {response.text})"
                )

    def has_mirror(self, mirror: dict) -> bool:
        try:
            return self.get_mirror_status(mirror) != "STATUS_UNKNOWN"
        except MirrorNotFound:
            return False

    def get_mirror_status(self, mirror: dict) -> str | None:
        url = f"{self._api_url}/v1/mirrors/status"
        data = {"flowJobName": mirror["flow_job_name"]}
        response = httpx.post(url, json=data, headers=self._headers)
        current_flow_state = response.json().get("currentFlowState")
        message = response.json().get("message", "")

        if response.status_code == 200:
            return current_flow_state
        elif (
            response.status_code == 500
            and "unable to get the workflow id of mirror" in message.lower()
        ):
            raise MirrorNotFound()
        else:
            raise Exception(
                f"Failed to get status of mirror '{mirror['flow_job_name']}' (error {response.status_code}: {response.text})"
            )

    def create_mirror(self, mirror: dict) -> None:
        if not self.has_mirror(mirror):
            url = f"{self._api_url}/v1/flows/cdc/create"
            data = {"connection_configs": mirror}
            response = httpx.post(url, json=data, headers=self._headers)
            workflow_id = response.json().get("workflowId")

            if not (response.status_code == 200 and workflow_id):
                raise Exception(
                    f"Failed to create mirror '{mirror['flow_job_name']}' (error {response.status_code}: {response.text})"
                )

    def drop_mirror(self, mirror: dict) -> None:
        if self.has_mirror(mirror):
            url = f"{self._api_url}/v1/mirrors/state_change"
            data = {
                "flowJobName": mirror["flow_job_name"],
                "requestedFlowState": "STATUS_TERMINATED",
            }
            response = httpx.post(url, json=data, headers=self._headers, timeout=None)

            if not (response.status_code == 200):
                raise Exception(
                    f"Failed to drop mirror '{mirror['flow_job_name']}' (error {response.status_code}: {response.text})"
                )


class SourcePeer(PostgresAdapter):
    def create_user(self, username: str, password: str) -> None:
        return super().create_user(
            username, password, options={"login": True, "replication": True}
        )


class DestinationPeer(ClickHouseAdapter):
    def __init__(self, db_settings: ClickHouseSettings, database: str) -> None:
        self._database = database
        super().__init__(db_settings)

    @property
    def database(self) -> str:
        return self._database
