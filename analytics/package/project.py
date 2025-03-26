from functools import cached_property
from package.config.constants import HOME_DIR, PROJECTS_DIR, TEMPLATE_PROJECT_DIR
from package.utils.filesystem import rmtree, symlink
from package.utils.template import render_template
from pathlib import Path
from prefect import get_client
from prefect.client.schemas.filters import DeploymentFilter, DeploymentFilterTags
from pydantic import BaseModel
from typing import List, Optional

import importlib
import os
import prefect
import re
import shutil


class Project:
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return f"Project '{self._name}'"

    @classmethod
    def from_name(cls, name):
        if not cls.exists(name):
            raise Exception(f"Project '{name}' not found")

        return cls(name)

    @classmethod
    def from_path(cls, path: Path | str) -> Optional["Project"]:
        name = cls.get_name_from_path(path)

        return cls.from_name(name)

    @classmethod
    def get_name_from_path(cls, path: Path | str) -> str:
        parent_dir = os.path.abspath(PROJECTS_DIR)
        child_dir = os.path.abspath(path)

        if os.path.isfile(child_dir):
            child_dir = os.path.dirname(child_dir)

        if (
            parent_dir == child_dir
            or os.path.commonpath([parent_dir, child_dir]) != parent_dir
        ):
            raise Exception(f"Path must be a subdirectory of {PROJECTS_DIR}")

        return os.path.relpath(child_dir, parent_dir).split(os.path.sep)[0]

    @classmethod
    def exists(cls, name: str) -> bool:
        return bool(
            [project for project in cls.list_projects() if project.name == name]
        )

    @classmethod
    def list_projects(cls) -> List["Project"]:
        return [cls(name) for name in list(os.listdir(PROJECTS_DIR))]

    @classmethod
    def validate_name(cls, name: str) -> bool:
        if not isinstance(name, str):
            raise Exception("Name must be a string")

        if len(name.strip()) < 1:
            raise Exception("Name must be 1 or more characters long")

        if not re.match("^[a-z0-9_]+$", name):
            raise Exception(
                "Name must contain only lowercase letters, numbers or underscore"
            )

        if not name[0].isalpha():
            raise Exception("Name must start with a letter")

        if name == "default":
            raise Exception(f"Name must not be '{name}'")

        return True

    @property
    def name(self) -> str:
        return self._name

    @cached_property
    def directory(self) -> Path:
        return Path(os.path.join(PROJECTS_DIR, self.name))

    @cached_property
    def dbt_directory(self) -> Path:
        return Path(os.path.join(self.directory, "dbt"))

    @cached_property
    def dbt_config_path(self) -> Path:
        return Path(os.path.join(self.directory, "dbt", "dbt_project.yml"))

    @cached_property
    def dbt_docs_directory(self) -> Path:
        return Path(os.path.join(self.directory, "dbt", "docs"))

    @cached_property
    def dbt_tests_directory(self) -> Path:
        return Path(os.path.join(self.directory, "dbt", "tests"))

    @cached_property
    def flows_directory(self) -> Path:
        return Path(os.path.join(self.directory, "flows"))

    @cached_property
    def notebooks_directory(self) -> Path:
        return Path(os.path.join(self.directory, "notebooks"))

    @cached_property
    def tests_directory(self) -> Path:
        return Path(os.path.join(self.directory, "tests"))

    @cached_property
    def peerdb_config_path(self) -> Path:
        return Path(os.path.join(self.directory, "peerdb.yaml"))

    @cached_property
    def prefect_config_path(self) -> Path:
        return Path(os.path.join(self.directory, "prefect.yaml"))

    @cached_property
    def settings(self) -> BaseModel:
        module = importlib.import_module(f"projects.{self._name}.config.settings")

        return module.get_settings()

    def init_directory(self):
        """Copy template project files to the project directory."""
        rmtree(self.directory)

        shutil.copytree(TEMPLATE_PROJECT_DIR, self.directory)

        context = {"project_name": self.name, "prefect_version": prefect.__version__}
        render_template(os.path.join(self.directory, "README.md"), context)
        render_template(os.path.join(self.directory, "prefect.yaml"), context)
        render_template(os.path.join(self.dbt_directory, "dbt_project.yml"), context)

    def sync_dbt_directory(self):
        """Copy global files to the project dbt directory."""
        symlink(
            os.path.join(HOME_DIR, ".sqlfluffignore"),
            os.path.join(self.dbt_directory, ".sqlfluffignore"),
        )

        rmtree(os.path.join(self.dbt_directory, "macros", "dbt"))
        shutil.copytree(
            os.path.join(TEMPLATE_PROJECT_DIR, "dbt", "macros", "dbt"),
            os.path.join(self.dbt_directory, "macros", "dbt"),
        )

    async def create(self):
        self.init_directory()
        self.sync_dbt_directory()

    async def refresh(self):
        self.sync_dbt_directory()

    async def delete(self):
        from package.cli.prefect_cli import delete_deployment

        async with get_client() as client:
            filter = DeploymentFilter(tags=DeploymentFilterTags(any_=[self.name]))
            deployments = await client.read_deployments(deployment_filter=filter)

            for deployment in deployments:
                await delete_deployment(client, deployment.id)

        rmtree(self.directory)
