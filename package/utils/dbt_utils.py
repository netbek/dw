from dbt.cli.main import dbtRunner, dbtRunnerResult
from package.config.constants import DBT_PROFILES_DIR
from package.project import Project
from package.types import DbtModel, DbtResourceType, DbtSeed, DbtSource
from package.utils.filesystem import get_file_extension
from package.utils.yaml_utils import safe_load_file
from pathlib import Path
from prefect_shell.commands import ShellOperation
from typing import Any, List, Optional

import json
import os

RE_REF = r"^ref\(['\"](.*?)['\"]\)$"
RE_SOURCE = r"^source\(['\"](.*?)['\"], ['\"](.*?)['\"]\)$"

RESOURCE_TYPE_TO_CLASS = {
    DbtResourceType.MODEL: DbtModel,
    DbtResourceType.SEED: DbtSeed,
    DbtResourceType.SOURCE: DbtSource,
}


def get_resource(project_dir: Path | str, name: str) -> DbtModel | DbtSeed | DbtSource | None:
    resources = list_resources(project_dir, select=name)

    if not resources:
        return None

    return resources[0]


def list_resources(
    project_dir: Path | str,
    resource_types: Optional[List[DbtResourceType]] = None,
    select: Optional[str] = None,
) -> List[DbtModel | DbtSeed | DbtSource]:
    valid_resource_types = RESOURCE_TYPE_TO_CLASS.keys()

    if resource_types is None:
        resource_types = valid_resource_types

    for resource_type in resource_types:
        if resource_type not in valid_resource_types:
            raise ValueError(f"'resource_types' must be any of: {", ".join(valid_resource_types)}")

    result = dbt_list_sync(
        project_dir,
        output="json",
        quiet=True,
        resource_types=resource_types,
        select=select,
    )
    resource_dicts = [json.loads(string) for string in result.result]

    cache = {}
    for resource in resource_dicts:
        if resource["resource_type"] == DbtResourceType.SOURCE:
            original_config = None
            path = resolve_resource_path(project_dir, resource)

            if path and get_file_extension(path) in [".yml", ".yaml"]:
                if path not in cache:
                    cache[path] = safe_load_file(path)

                for source in cache[path]["sources"]:
                    if source["name"] == resource["source_name"]:
                        for table in source["tables"]:
                            if table["name"] == resource["name"]:
                                original_config = table
                                break
                    if original_config:
                        break

            resource["original_config"] = original_config

    resources = []
    for resource in resource_dicts:
        class_ = RESOURCE_TYPE_TO_CLASS[resource["resource_type"]]
        resources.append(class_(**resource))

    return resources


def resolve_resource_path(project_dir: str, resource: dict) -> str | None:
    project_name = Project.get_name_from_path(project_dir)

    if resource["package_name"] == project_name:
        path = os.path.join(project_dir, resource["original_file_path"])
    else:
        path = os.path.join(project_dir, "dbt_packages", resource["original_file_path"])

    if os.path.exists(path):
        return path


def dbt_list_command(
    project_dir: Path | str,
    debug: Optional[bool] = False,
    exclude: Optional[str] = None,
    fail_fast: Optional[bool] = True,
    models: Optional[str] = None,
    output: Optional[str] = None,
    quiet: Optional[bool] = False,
    resource_types: Optional[List[DbtResourceType]] = None,
    select: Optional[str] = None,
    selector: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
    vars: Optional[dict[str, Any]] = None,
) -> list[str]:
    cmd = ["dbt", "list", "--profiles-dir", DBT_PROFILES_DIR, "--project-dir", str(project_dir)]

    if debug:
        cmd.extend(["--debug"])
    else:
        cmd.extend(["--no-debug"])

    if exclude:
        cmd.extend(["--exclude", exclude])

    if fail_fast:
        cmd.extend(["--fail-fast"])
    else:
        cmd.extend(["--no-fail-fast"])

    if models:
        cmd.extend(["--models", models])

    if output:
        cmd.extend(["--output", output])

    if quiet:
        cmd.extend(["--quiet"])
    else:
        cmd.extend(["--no-quiet"])

    if resource_types:
        for resource_type in resource_types:
            cmd.extend(["--resource-type", resource_type])

    if select:
        cmd.extend(["--select", select])

    if selector:
        cmd.extend(["--selector", selector])

    if target:
        cmd.extend(["--target", target])

    if use_colors:
        cmd.extend(["--use-colors"])
    else:
        cmd.extend(["--no-use-colors"])

    if vars:
        cmd.extend(["--vars", f"'{json.dumps(vars)}'"])

    return cmd


def dbt_list_sync(
    project_dir: str,
    debug: Optional[bool] = False,
    exclude: Optional[str] = None,
    fail_fast: Optional[bool] = True,
    models: Optional[str] = None,
    output: Optional[str] = None,
    quiet: Optional[bool] = False,
    resource_types: Optional[List[DbtResourceType]] = None,
    select: Optional[str] = None,
    selector: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
    vars: Optional[dict[str, Any]] = None,
) -> dbtRunnerResult:
    cmd = dbt_list_command(
        project_dir=project_dir,
        debug=debug,
        exclude=exclude,
        fail_fast=fail_fast,
        models=models,
        output=output,
        quiet=quiet,
        resource_types=resource_types,
        select=select,
        selector=selector,
        target=target,
        use_colors=use_colors,
        vars=vars,
    )

    return dbtRunner().invoke(cmd[1:])


def dbt_run_command(
    project_dir: Path | str,
    debug: Optional[bool] = False,
    exclude: Optional[str] = None,
    fail_fast: Optional[bool] = True,
    full_refresh: Optional[bool] = False,
    models: Optional[str] = None,
    quiet: Optional[bool] = False,
    select: Optional[str] = None,
    selector: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
    vars: Optional[dict[str, Any]] = None,
) -> list[str]:
    cmd = ["dbt", "run", "--profiles-dir", DBT_PROFILES_DIR, "--project-dir", str(project_dir)]

    if debug:
        cmd.extend(["--debug"])
    else:
        cmd.extend(["--no-debug"])

    if exclude:
        cmd.extend(["--exclude", exclude])

    if fail_fast:
        cmd.extend(["--fail-fast"])
    else:
        cmd.extend(["--no-fail-fast"])

    if full_refresh:
        cmd.extend(["--full-refresh"])

    if models:
        cmd.extend(["--models", models])

    if quiet:
        cmd.extend(["--quiet"])
    else:
        cmd.extend(["--no-quiet"])

    if select:
        cmd.extend(["--select", select])

    if selector:
        cmd.extend(["--selector", selector])

    if target:
        cmd.extend(["--target", target])

    if use_colors:
        cmd.extend(["--use-colors"])
    else:
        cmd.extend(["--no-use-colors"])

    if vars:
        cmd.extend(["--vars", f"'{json.dumps(vars)}'"])

    return cmd


async def dbt_run_async(
    project_dir: str,
    debug: Optional[bool] = False,
    exclude: Optional[str] = None,
    fail_fast: Optional[bool] = True,
    full_refresh: Optional[bool] = False,
    models: Optional[str] = None,
    quiet: Optional[bool] = False,
    select: Optional[str] = None,
    selector: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
    vars: Optional[dict[str, Any]] = None,
) -> str:
    cmd = dbt_run_command(
        project_dir=project_dir,
        debug=debug,
        fail_fast=fail_fast,
        full_refresh=full_refresh,
        exclude=exclude,
        models=models,
        quiet=quiet,
        select=select,
        selector=selector,
        target=target,
        use_colors=use_colors,
        vars=vars,
    )

    async with ShellOperation(commands=[" ".join(cmd)], working_dir=project_dir) as op:
        process = await op.trigger()
        await process.wait_for_completion()
        result = await process.fetch_result()

    return result


def dbt_run_sync(
    project_dir: str,
    debug: Optional[bool] = False,
    exclude: Optional[str] = None,
    fail_fast: Optional[bool] = True,
    full_refresh: Optional[bool] = False,
    models: Optional[str] = None,
    quiet: Optional[bool] = False,
    select: Optional[str] = None,
    selector: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
    vars: Optional[dict[str, Any]] = None,
) -> dbtRunnerResult:
    cmd = dbt_run_command(
        project_dir=project_dir,
        debug=debug,
        fail_fast=fail_fast,
        full_refresh=full_refresh,
        exclude=exclude,
        models=models,
        quiet=quiet,
        select=select,
        selector=selector,
        target=target,
        use_colors=use_colors,
        vars=vars,
    )

    return dbtRunner().invoke(cmd[1:])


def dbt_seed_command(
    project_dir: Path | str,
    debug: Optional[bool] = False,
    fail_fast: Optional[bool] = True,
    quiet: Optional[bool] = False,
    select: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
) -> list[str]:
    cmd = ["dbt", "seed", "--profiles-dir", DBT_PROFILES_DIR, "--project-dir", str(project_dir)]

    if debug:
        cmd.extend(["--debug"])
    else:
        cmd.extend(["--no-debug"])

    if fail_fast:
        cmd.extend(["--fail-fast"])
    else:
        cmd.extend(["--no-fail-fast"])

    if quiet:
        cmd.extend(["--quiet"])
    else:
        cmd.extend(["--no-quiet"])

    if select:
        cmd.extend(["--select", select])

    if target:
        cmd.extend(["--target", target])

    if use_colors:
        cmd.extend(["--use-colors"])
    else:
        cmd.extend(["--no-use-colors"])

    return cmd


def dbt_seed_sync(
    project_dir: str,
    debug: Optional[bool] = False,
    fail_fast: Optional[bool] = True,
    quiet: Optional[bool] = False,
    select: Optional[str] = None,
    target: Optional[str] = None,
    use_colors: Optional[bool] = False,
) -> dbtRunnerResult:
    cmd = dbt_seed_command(
        project_dir=project_dir,
        debug=debug,
        fail_fast=fail_fast,
        quiet=quiet,
        select=select,
        target=target,
        use_colors=use_colors,
    )

    return dbtRunner().invoke(cmd[1:])
