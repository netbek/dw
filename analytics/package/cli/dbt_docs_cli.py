from livereload import Server
from package.project import Project
from package.utils.filesystem import find_up

import json
import os
import rich.console
import subprocess
import typer

docs_app = typer.Typer(name="docs", add_completion=False)
docs_app.console = rich.console.Console()


@docs_app.command()
def generate():
    cwd = os.getcwd()
    dbt_project_file = find_up(cwd, "dbt_project.yml")

    if not dbt_project_file:
        raise Exception(f"No dbt_project.yml found in {cwd} or higher")

    project = Project.from_path(cwd)

    cmd = ["dbt", "docs", "generate"]
    try:
        output = (
            subprocess.check_output(cmd, cwd=project.dbt_directory).decode().strip()
        )
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode().strip()
        print(output)
        raise exc

    bundle_docs(project.dbt_directory)
    docs_app.console.print(
        f"Generated docs '{project.dbt_docs_directory}'", style="green"
    )


@docs_app.command()
def serve():
    cwd = os.getcwd()
    dbt_project_file = find_up(cwd, "dbt_project.yml")

    if not dbt_project_file:
        raise Exception(f"No dbt_project.yml found in {cwd} or higher")

    project = Project.from_path(cwd)

    # If the docs page has not been generated before, then do so now
    if not os.path.exists(os.path.join(project.dbt_docs_directory, "index.html")):
        generate()

    watch_paths = [project.dbt_config_path]
    for path in project.settings.dbt.config["macro-paths"]:
        watch_paths.extend(
            [
                os.path.join(project.dbt_directory, path, "**", "*.sql"),
            ]
        )
    for path in project.settings.dbt.config["model-paths"]:
        watch_paths.extend(
            [
                os.path.join(project.dbt_directory, path, "**", "*.sql"),
                os.path.join(project.dbt_directory, path, "**", "*.yml"),
            ]
        )

    # Start the LiveReload server
    server = Server()
    for path in watch_paths:
        server.watch(path, generate)
    server.serve(host="0.0.0.0", port=8080, root=project.dbt_docs_directory)


def bundle_docs(dbt_dir: str):
    """
    Transform output from `dbt docs generate` into a single HTML file.

    Source: https://data-banana.github.io/dbt-generate-doc-in-one-static-html-file.html
    """
    html_path = os.path.join(dbt_dir, "target", "index.html")
    manifest_path = os.path.join(dbt_dir, "target", "manifest.json")
    catalog_path = os.path.join(dbt_dir, "target", "catalog.json")
    dest_path = os.path.join(dbt_dir, "docs", "index.html")

    with open(html_path, "rt") as fp:
        html = fp.read()

    with open(manifest_path, "rt") as fp:
        manifest = json.load(fp)

    with open(catalog_path, "rt") as fp:
        catalog = json.load(fp)

    search_str = 'n=[o("manifest","manifest.json"+t),o("catalog","catalog.json"+t)]'
    replace_str = (
        "n=[{label: 'manifest', data: "
        + json.dumps(manifest)
        + "},{label: 'catalog', data: "
        + json.dumps(catalog)
        + "}]"
    )
    html = html.replace(search_str, replace_str)

    with open(dest_path, "wt") as fp:
        fp.write(html)
