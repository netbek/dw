FROM python:3.12.10-slim-bookworm AS python-builder
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    gcc git libpq-dev python-dev-is-python3

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY pyproject.toml /build/pyproject.toml
COPY uv.lock /build/uv.lock

WORKDIR /build

RUN uv venv ${VIRTUAL_ENV} && \
    uv sync --active --frozen --all-groups

RUN apt-get purge --yes \
    gcc git libpq-dev python-dev-is-python3 && \
    apt-get autoremove --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

####################################################################################################

FROM prefecthq/prefect:3.0.10-python3.12 AS prefect-common
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

ARG DOCKER_UID
ARG DOCKER_GID

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    bash-completion ca-certificates curl git less man-db nano openssh-client

ENV DOCKER_USER=analyst
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

WORKDIR /usr/local/dbt
RUN curl -O https://raw.githubusercontent.com/dbt-labs/dbt-completion.bash/915cdc5e301f5bc4c89324d3bd790320476728cf/dbt-completion.bash

RUN groupadd ${DOCKER_USER} --gid ${DOCKER_GID} && \
    useradd ${DOCKER_USER} --create-home --gid ${DOCKER_GID} --uid ${DOCKER_UID} --shell /bin/false && \
    echo "\n${DOCKER_USER} ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown --recursive ${DOCKER_UID}:${DOCKER_GID} /home/${DOCKER_USER}

RUN apt-get autoremove --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ${DOCKER_USER}
WORKDIR /home/${DOCKER_USER}

####################################################################################################

FROM python:3.12.10-slim-bookworm AS jupyter
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

ARG DOCKER_UID
ARG DOCKER_GID

ENV DOCKER_USER=analyst
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

RUN groupadd ${DOCKER_USER} --gid ${DOCKER_GID} && \
    useradd ${DOCKER_USER} --create-home --gid ${DOCKER_GID} --uid ${DOCKER_UID} --shell /bin/false && \
    echo "\n${DOCKER_USER} ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown --recursive ${DOCKER_UID}:${DOCKER_GID} /home/${DOCKER_USER}

USER ${DOCKER_USER}
WORKDIR /home/${DOCKER_USER}

EXPOSE 8888
CMD ["jupyter", "nbclassic", "--ip='0.0.0.0'", "--port=8888", "--no-browser"]

####################################################################################################

FROM python:3.12.10-slim-bookworm AS api
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

ARG DOCKER_UID
ARG DOCKER_GID

ENV DOCKER_USER=analyst
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

RUN groupadd ${DOCKER_USER} --gid ${DOCKER_GID} && \
    useradd ${DOCKER_USER} --create-home --gid ${DOCKER_GID} --uid ${DOCKER_UID} --shell /bin/false && \
    echo "\n${DOCKER_USER} ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown --recursive ${DOCKER_UID}:${DOCKER_GID} /home/${DOCKER_USER}

USER ${DOCKER_USER}
WORKDIR /home/${DOCKER_USER}

EXPOSE 80
