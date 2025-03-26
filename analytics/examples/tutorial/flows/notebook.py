from prefect import flow, get_run_logger
from prefect_jupyter import notebook
from projects.tutorial.config.settings import get_settings

import os

settings = get_settings()


@flow(name="tutorial__notebook_flow")
def notebook_flow(greeting: str):
    nb = notebook.execute_notebook(
        os.path.join(settings.notebook.directory, "greet.ipynb"),
        parameters={"greeting": greeting},
    )
    body = notebook.export_notebook(nb)
    export_path = os.path.join(settings.notebook.directory, "export", "greet.ipynb")
    with open(export_path, "w") as file:
        file.write(body)
    logger = get_run_logger()
    logger.info(f"Exported notebook to {export_path}")


if __name__ == "__main__":
    notebook_flow()
