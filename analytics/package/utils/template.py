from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class EnvVars(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=list(Path("/usr/local/share/dw").glob("*.env")),
        extra="allow",
        case_sensitive=True,
    )


def env_var(var: str, default: Optional[str] = None) -> str:
    return getattr(EnvVars(), var, default)


def render_jinja_template(file_path: str, context: Optional[dict] = None) -> str:
    env = Environment(loader=FileSystemLoader("/"))
    env.globals["env_var"] = env_var
    template = env.get_template(str(file_path))

    return template.render(context or {})


def render_template(file_path: str, context: dict):
    """
    TODO Consider replacing with Jinja if it's possible to preserve unescaped delimiters, e.g.
    {{ }} for expressions. This function is meant to render the given context only, not everything
    in the template.
    """
    with open(file_path, "rt") as file:
        template = file.read()

    for variable, value in context.items():
        template = template.replace("{{ " + variable + " }}", value)

    with open(file_path, "wt") as file:
        file.write(template)
