from package.cli.dbt_docs_cli import docs_app
from package.cli.root import app
from package.config.constants import CODEGEN_TO_CLICKHOUSE_DATA_TYPE
from package.dbt import Dbt
from package.project import Project
from package.types import DbtResourceType
from package.utils.filesystem import find_up
from package.utils.yaml_utils import safe_load_file
from pathlib import Path

import dbt.version
import json
import os
import pydash
import subprocess
import typer
import yaml

dbt_app = typer.Typer(name="dbt", add_completion=False)
dbt_app.add_typer(docs_app)
app.add_typer(dbt_app)


@dbt_app.command(help="Print version.")
def version():
    app.console.print(dbt.version.__version__)


@dbt_app.command(help="Generate model YAML.")
def model_yaml(models: list[str]):
    cwd = os.getcwd()
    dbt_project_file = find_up(cwd, "dbt_project.yml")

    if not dbt_project_file:
        raise Exception(f"No dbt_project.yml found in {cwd} or higher")

    project = Project.from_path(cwd)
    dbt = Dbt(project.dbt_directory)
    resources = dbt.list_resources(resource_types=[DbtResourceType.MODEL])

    for model in models:
        resource = pydash.find(resources, lambda resource: resource.name == model)

        if not resource:
            continue

        model_name = resource.name
        model_path = Path(
            os.path.join(project.dbt_directory, resource.original_file_path)
        )
        schema_path = os.path.join(model_path.parent, "schema", f"{model_name}.yml")
        schema_dir = os.path.dirname(schema_path)

        os.makedirs(schema_dir, exist_ok=True)

        # Load existing schema
        if os.path.exists(schema_path):
            schema = safe_load_file(schema_path)
        else:
            schema = {"version": 2, "models": []}

        # Build model
        cmd = [
            "dbt",
            "--fail-fast",
            "--quiet",
            "run",
            "-m",
            model_name,
            "--full-refresh",
        ]
        try:
            subprocess.check_output(cmd, cwd=project.dbt_directory)
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode().strip()
            app.console.print(output, style="red")
            raise exc

        # Generate schema YAML
        cmd = [
            "dbt",
            "--quiet",
            "run-operation",
            "generate_model_yaml",
            "--args",
            json.dumps({"model_names": [model_name]}),
        ]
        try:
            output = (
                subprocess.check_output(cmd, cwd=project.dbt_directory).decode().strip()
            )
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode().strip()
            app.console.print(output, style="red")
            raise exc

        new_model = yaml.safe_load(output)["models"][0]
        new_model = {
            "name": new_model["name"],
            "columns": [
                {
                    "name": column["name"],
                    "data_type": CODEGEN_TO_CLICKHOUSE_DATA_TYPE.get(
                        column["data_type"], column["data_type"]
                    ),
                }
                for column in new_model["columns"]
            ],
        }

        old_model_indexes = [
            i for i, model in enumerate(schema["models"]) if model["name"] == model_name
        ]

        if old_model_indexes:
            schema["models"][old_model_indexes[0]] = new_model
        else:
            schema["models"].append(new_model)

        schema["models"] = sorted(schema["models"], key=lambda x: x["name"])

        # Write schema file
        with open(schema_path, "wt") as fp:
            data = yaml.safe_dump(schema, sort_keys=False)
            fp.write(data)
