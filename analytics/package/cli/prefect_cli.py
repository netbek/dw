from enum import Enum
from package.cli.root import app
from package.config.constants import PREFECT_PROFILES_PATH, PREFECT_PROVISION_PATH
from package.project import Project
from package.utils.typer_utils import typer_async
from package.utils.yaml_utils import safe_load_file
from prefect import get_client
from prefect.client.orchestration import PrefectClient
from prefect.client.schemas.actions import WorkPoolCreate, WorkPoolUpdate
from starlette import status
from typing import Optional
from uuid import UUID

import httpx
import os
import prefect
import pydash
import subprocess
import typer

prefect_app = typer.Typer(name="prefect", add_completion=False)
app.add_typer(prefect_app)


class DeployAction(str, Enum):
    create = "create"


class DeploymentAction(str, Enum):
    delete = "delete"
    pause = "pause"
    resume = "resume"


class DeploymentNotFoundError(Exception):
    def __init__(self, message="Deployment not found"):
        self.message = message
        super().__init__(self.message)


class ProfileNotFoundError(Exception):
    def __init__(self, message="Profile not found in config"):
        self.message = message
        super().__init__(self.message)


@prefect_app.command()
def version():
    print(prefect.__version__)


@prefect_app.command()
@typer_async
async def provision(
    profile_name: Optional[str] = typer.Argument(
        None, help="Profile name. Default is the active profile."
    ),
):
    profiles = prefect.settings.load_profiles()
    current_profile = prefect.context.get_settings_context().profile
    current_name = current_profile.name if current_profile is not None else None
    provision_profiles = safe_load_file(PREFECT_PROVISION_PATH).get("profiles", {})

    if profile_name:
        if profile_name not in profiles:
            raise ProfileNotFoundError(
                f"Profile '{profile_name}' not found in {PREFECT_PROFILES_PATH}"
            )

        if profile_name not in provision_profiles:
            raise ProfileNotFoundError(
                f"Profile '{profile_name}' not found in {PREFECT_PROVISION_PATH}"
            )
    else:
        if current_name:
            profile_name = current_name
        else:
            raise Exception("Specify a profile because none are active")

    work_pools = provision_profiles[profile_name].get("work_pools", {})
    work_pools = [{"name": k, **v} for k, v in work_pools.items()]
    names = [work_pool["name"] for work_pool in work_pools]

    async with get_client() as client:
        existing = await client.read_work_pools()
        existing_names = [work_pool.name for work_pool in existing]

        # Delete existing work pools that aren't in configuration
        delete_names = [name for name in existing_names if name not in names]

        if delete_names:
            for name in delete_names:
                await client.delete_work_pool(name)
                app.console.print(f"Deleted work pool '{name}'", style="green")

        # Create or update work pools
        for work_pool in work_pools:
            if work_pool["name"] in existing_names:
                await client.update_work_pool(
                    work_pool["name"],
                    WorkPoolUpdate(concurrency_limit=work_pool["concurrency_limit"]),
                )
                app.console.print(
                    f"Updated work pool '{work_pool['name']}'", style="green"
                )
            else:
                await client.create_work_pool(WorkPoolCreate(**work_pool))
                app.console.print(
                    f"Created work pool '{work_pool['name']}'", style="green"
                )


@prefect_app.command()
@typer_async
async def deploy(
    project_names: Optional[list[str]] = typer.Option(
        None, "-p", "--project-name", help="1 or more project names"
    ),
    deployment_names: Optional[list[str]] = typer.Option(
        None, "-d", "--deployment-name", help="1 or more deployment names"
    ),
    pause: Optional[bool] = typer.Option(
        False,
        "--pause",
        help="Whether to create a paused deployment. By default, new deployments are active.",
    ),
):
    if not project_names and not deployment_names:
        raise Exception("1 or more project names and/or deployment names is required.")

    deploy_configs = _load_deploy_configs(
        project_names=project_names, deployment_names=deployment_names
    )
    selected_names = [deployment["name"] for deployment in deploy_configs]

    if not selected_names:
        raise Exception(
            "No deployments match the given project names and/or deployment names. "
            "Check the prefect.yaml configs."
        )

    async with get_client() as client:
        existing = await client.read_deployments()
        existing_names = [d.name for d in existing]

        try:
            deployment_actions = _build_deployment_actions(
                DeployAction.create, selected_names, existing_names
            )
        except Exception as exc:
            app.console.print(exc.message, style="red")
            return

        create_names = [
            d["name"] for d in deployment_actions if d["action"] == DeployAction.create
        ]

        for name in create_names:
            create_deployments = [
                deployment
                for deployment in deploy_configs
                if deployment["name"] == name
            ]

            for deployment in create_deployments:
                cmd = [
                    "prefect",
                    "--no-prompt",
                    "deploy",
                    "--name",
                    deployment["name"],
                ]
                cwd = os.path.dirname(deployment["config_path"])
                subprocess.check_output(cmd, cwd=cwd)

            deployments = await client.read_deployments()
            deployments = [d for d in deployments if d.name == name]

            for deployment in deployments:
                app.console.print(
                    f"Created deployment '{deployment.name}'", style="green"
                )

                if pause:
                    await client.set_deployment_paused_state(deployment.id, True)
                    app.console.print(
                        f"Paused deployment '{deployment.name}'", style="green"
                    )

        update_names = [
            d["name"]
            for d in deployment_actions
            if d["action"] == DeploymentAction.resume
        ]
        update_deployments = [d for d in existing if d.name in update_names]

        for deployment in update_deployments:
            if pause:
                await client.set_deployment_paused_state(deployment.id, True)
                app.console.print(
                    f"Paused deployment '{deployment.name}'", style="green"
                )
            else:
                await client.set_deployment_paused_state(deployment.id, False)
                app.console.print(
                    f"Resumed deployment '{deployment.name}'", style="green"
                )


@prefect_app.command()
@typer_async
async def deployment(
    action: DeploymentAction,
    project_names: Optional[list[str]] = typer.Option(
        None, "-p", "--project-name", help="1 or more project names"
    ),
    deployment_names: Optional[list[str]] = typer.Option(
        None, "-d", "--deployment-name", help="1 or more deployment names"
    ),
):
    if not project_names and not deployment_names:
        raise Exception("1 or more project names and/or deployment names is required.")

    deploy_configs = _load_deploy_configs(
        project_names=project_names, deployment_names=deployment_names
    )
    selected_names = [deployment["name"] for deployment in deploy_configs]

    if not selected_names:
        raise Exception(
            "No deployments match the given project names and/or deployment names. "
            "Check the prefect.yaml configs."
        )

    async with get_client() as client:
        existing = await client.read_deployments()
        existing_names = [d.name for d in existing]

        if action == DeploymentAction.delete:
            # Remove selected deployments that have not been deployed
            selected_names = pydash.intersection(selected_names, existing_names)

        try:
            deployment_actions = _build_deployment_actions(
                action, selected_names, existing_names
            )
        except Exception as exc:
            app.console.print(exc.message, style="red")
            return

        deployment_names = [
            d["name"] for d in deployment_actions if d["action"] == action
        ]
        deployments = [d for d in existing if d.name in deployment_names]

        for deployment in deployments:
            if action == DeploymentAction.delete:
                await delete_deployment(client, deployment.id)
            elif action == DeploymentAction.pause:
                await pause_deployment(client, deployment.id)
            elif action == DeploymentAction.resume:
                await resume_deployment(client, deployment.id)


async def delete_deployment(client: PrefectClient, deployment_id: UUID):
    deployment = await client.read_deployment(deployment_id)

    await client.delete_deployment(deployment.id)
    app.console.print(f"Deleted deployment '{deployment.name}'", style="green")

    flows = await client.read_flows()
    flows = [flow for flow in flows if flow.id == deployment.flow_id]

    for flow in flows:
        # Get a list of deployments of the flow other than the given deployment
        other_deployments = await client.read_deployments()
        other_deployments = [
            d
            for d in other_deployments
            if d.flow_id == flow.id and d.id != deployment.id
        ]

        if not other_deployments:
            await delete_flow(client, flow.id)
            app.console.print(f"Deleted flow '{flow.name}'", style="green")


async def pause_deployment(client: PrefectClient, deployment_id: UUID):
    deployment = await client.read_deployment(deployment_id)

    await client.set_deployment_paused_state(deployment.id, True)
    app.console.print(f"Paused deployment '{deployment.name}'", style="green")


async def resume_deployment(client: PrefectClient, deployment_id: UUID):
    deployment = await client.read_deployment(deployment_id)

    await client.set_deployment_paused_state(deployment.id, False)
    app.console.print(f"Resumed deployment '{deployment.name}'", style="green")


# TODO Remove after delete_flow() has been added to PrefectClient
async def delete_flow(client: PrefectClient, flow_id: UUID):
    try:
        await client._client.delete(f"/flows/{flow_id}")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise prefect.exceptions.ObjectNotFound(http_exc=exc) from exc
        else:
            raise


def _load_deploy_configs(
    project_names: Optional[list[str]] = None,
    deployment_names: Optional[list[str]] = None,
):
    deploy_configs = []
    all_projects = Project.list_projects()

    if project_names:
        selected_projects = [
            project for project in all_projects if project.name in project_names
        ]
    else:
        selected_projects = all_projects

    for project in selected_projects:
        deployments = project.settings.prefect.config.get("deployments") or {}

        for deployment in deployments:
            if deployment_names and deployment["name"] not in deployment_names:
                continue

            deploy_configs.append(
                {
                    **deployment,
                    "project_name": project.name,
                    "config_path": project.prefect_config_path,
                }
            )

    return deploy_configs


def _build_deployment_actions(
    action: DeployAction | DeploymentAction,
    selected_names: list[str],
    existing_names: Optional[list[str]] = None,
):
    result = []

    if not existing_names:
        existing_names = []

    if action == DeployAction.create:
        for name in selected_names:
            if name in existing_names:
                result.append({"action": DeploymentAction.resume, "name": name})
            else:
                result.append({"action": DeployAction.create, "name": name})
    else:
        not_found = []

        for name in selected_names:
            if name in existing_names:
                result.append({"action": action, "name": name})
            else:
                not_found.append(name)

        if not_found:
            quoted = list(map(lambda x: f"'{x}'", not_found))
            raise DeploymentNotFoundError(f"Deployment {', '.join(quoted)} not found")

    return result
