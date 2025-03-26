from package.cli.root import app
from package.config.constants import DBT_PROFILES_FILE, HOME_DIR
from package.project import Project
from package.utils.typer_utils import typer_async

import os
import subprocess
import typer

project_app = typer.Typer(name="project", add_completion=False)
app.add_typer(project_app)


@project_app.command()
@typer_async
async def init(project_name: str):
    if Project.exists(project_name):
        raise Exception(f"Project '{project_name}' already exists")

    Project.validate_name(project_name)

    await Project(project_name).create()

    app.console.print(
        f"To complete the setup, perform these steps:\n"
        f"1. Add env variables for '{project_name}' to ./template_env/<PROFILE>/database.env\n"
        f"2. Run './scripts/env.sh PROFILE -f'\n"
        f"3. Add a profile for '{project_name}' to {DBT_PROFILES_FILE}\n"
        f"4. Stop and restart the containers\n"
        f"5. Run './scripts/cli.sh project refresh {project_name}'"
    )


@project_app.command()
@typer_async
async def delete(project_name: str):
    project = Project.from_name(project_name)

    confirmed = typer.confirm(
        "Are you sure you want to delete the project's files and data?"
    )
    if not confirmed:
        raise typer.Abort()

    await project.delete()

    app.console.print(
        f"To complete the deletion, perform these steps:\n"
        f"1. Remove env variables for '{project_name}' from ./template_env/<PROFILE>/database.env\n"
        f"2. Run './scripts/env.sh PROFILE -f'\n"
        f"3. Remove the profile for '{project_name}' from {DBT_PROFILES_FILE}\n"
        f"4. Stop and restart the containers\n"
    )


@project_app.command()
@typer_async
async def refresh(project_name: str):
    project = Project.from_name(project_name)

    await project.refresh()

    subprocess.run("dbt clean", shell=True, cwd=project.dbt_directory)
    subprocess.run("dbt deps", shell=True, cwd=project.dbt_directory)
    subprocess.run("dbt run -s tag:dbt_audit", shell=True, cwd=project.dbt_directory)
    subprocess.run("dbt seed", shell=True, cwd=project.dbt_directory)


@project_app.command()
def lint(project_name: str):
    project = Project.from_name(project_name)
    yamllint_config_file = os.path.join(HOME_DIR, ".yamllint")
    sqlfluff_config_file = os.path.join(HOME_DIR, ".sqlfluff")

    subprocess.run(
        f"yamllint -c {yamllint_config_file} .", shell=True, cwd=project.dbt_directory
    )
    subprocess.run(
        f"sqlfluff lint --config {sqlfluff_config_file} --ignore-local-config --ignore parsing .",
        shell=True,
        cwd=project.dbt_directory,
    )


@project_app.command()
def fix(project_name: str):
    project = Project.from_name(project_name)
    sqlfluff_config_file = os.path.join(HOME_DIR, ".sqlfluff")

    subprocess.run(
        f"sqlfluff fix --config {sqlfluff_config_file} --ignore-local-config --ignore parsing .",
        shell=True,
        cwd=project.dbt_directory,
    )


@project_app.command()
def test(project_name: str):
    project = Project.from_name(project_name)

    subprocess.run("dbt test -t test -q", shell=True, cwd=project.dbt_directory)
    subprocess.run("pytest", shell=True, cwd=os.path.join(project.directory, "tests"))
