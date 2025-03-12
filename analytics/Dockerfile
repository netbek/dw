FROM python:3.12.7-slim-bookworm AS python-builder

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    gcc git libpq-dev python-dev-is-python3

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN python -m venv ${VIRTUAL_ENV}

COPY requirements_api.txt /build/requirements_api.txt
COPY requirements_base.txt /build/requirements_base.txt
COPY requirements_dev.txt /build/requirements_dev.txt
COPY requirements_jupyter.txt /build/requirements_jupyter.txt

RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir --requirement /build/requirements_base.txt && \
    pip install --no-cache-dir --requirement /build/requirements_dev.txt

RUN apt-get purge --yes \
    gcc git libpq-dev patch python-dev-is-python3
RUN apt-get autoremove --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

####################################################################################################

FROM prefecthq/prefect:3.2.12-python3.12 AS prefect-common

ARG DOCKER_UID
ARG DOCKER_GID

ENV DOCKER_USER=analyst

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    bash-completion ca-certificates curl git less man-db nano openssh-client

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

# This is only needed to make IntelliSense in the VS Code dev container work for the API packages
# This could be removed if using multiple containers: https://code.visualstudio.com/remote/advancedcontainers/connect-multiple-containers
RUN pip install --no-cache-dir --requirement /build/requirements_api.txt

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

FROM python:3.12.7-slim-bookworm AS jupyter

ARG DOCKER_UID
ARG DOCKER_GID

ENV DOCKER_USER=analyst

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

RUN pip install --no-cache-dir --requirement /build/requirements_jupyter.txt

RUN groupadd ${DOCKER_USER} --gid ${DOCKER_GID} && \
    useradd ${DOCKER_USER} --create-home --gid ${DOCKER_GID} --uid ${DOCKER_UID} --shell /bin/false && \
    echo "\n${DOCKER_USER} ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown --recursive ${DOCKER_UID}:${DOCKER_GID} /home/${DOCKER_USER}

RUN apt-get autoremove --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ${DOCKER_USER}
WORKDIR /home/${DOCKER_USER}

EXPOSE 8888
CMD ["jupyter", "nbclassic", "--ip='0.0.0.0'", "--port=8888", "--no-browser"]

####################################################################################################

FROM python:3.12.7-slim-bookworm AS api

ARG DOCKER_UID
ARG DOCKER_GID

ENV DOCKER_USER=analyst

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
COPY --from=python-builder "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=python-builder /build /build

RUN pip install --no-cache-dir --requirement /build/requirements_api.txt

RUN groupadd ${DOCKER_USER} --gid ${DOCKER_GID} && \
    useradd ${DOCKER_USER} --create-home --gid ${DOCKER_GID} --uid ${DOCKER_UID} --shell /bin/false && \
    echo "\n${DOCKER_USER} ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown --recursive ${DOCKER_UID}:${DOCKER_GID} /home/${DOCKER_USER}

RUN apt-get autoremove --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ${DOCKER_USER}
WORKDIR /home/${DOCKER_USER}

EXPOSE 80
