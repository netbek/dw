# Installation

## Prerequisites

1. [Postgres v13 or higher](https://www.postgresql.org/about/news/postgresql-13-released-2077/).

    Enable replication on the Postgres server.

    | Setting                      | Recommended value  |
    |------------------------------|--------------------|
    | wal_level                    | logical            |
    | max_wal_senders              | > 1                |
    | max_replication_slots        | >= 4               |

    To get the current settings, run this query:

    ```sql
    select name, setting
    from pg_settings
    where name in ('wal_level', 'max_wal_senders', 'max_replication_slots');
    ```

    To update the settings, amend `postgresql.conf` on the Postgres server and restart the server:

    ```shell
    wal_level = 'logical'
    max_wal_senders = '2'
    max_replication_slots = '4'
    ```

## Development

### Install

1. Install [Docker Engine v23 or higher](https://docs.docker.com/engine/install/) and [Docker Compose v2 or higher](https://docs.docker.com/compose/install/). Follow the links for instructions or run this script:

    ```shell
    ./scripts/install.sh docker
    ```

2. Install [Tilt v0.33.20 or higher](https://docs.tilt.dev/install). Follow the link for instructions or run this script:

    ```shell
    ./scripts/install.sh tilt
    ```

3. Install PeerDB:

    ```shell
    ./scripts/install.sh peerdb
    ```

4. Install a deployment configuration:

    ```shell
    ./scripts/deployment-install.sh <REPOSITORY_URL> <BRANCH_NAME>
    ```

5. For each project, clone its repo:

    ```shell
    cd analytics/projects
    git clone <REPOSITORY_URL> <PROJECT_NAME>
    ```

6. Start the services:

    ```shell
    tilt up --port 29000
    ```

    Wait a few minutes for the Docker images to be built. To check the progress, open [http://localhost:29000](http://localhost:29000).

7. Run the provision script to configure Prefect:

    ```shell
    ./scripts/cli.sh prefect provision dev
    ```

8. For each project, install its dependencies:

    ```shell
    ./scripts/cli.sh project refresh <PROJECT_NAME>
    ```

9. For each project that has database syncing, set up PeerDB and sync the ClickHouse database:

    ```shell
    ./scripts/cli.sh peerdb install <PROJECT_NAME>
    ```

    To check the progress, open [http://localhost:3000/mirrors](http://localhost:3000/mirrors).

### Optional extras

#### VS Code

Download [VS Code](https://code.visualstudio.com/). After installing VS Code, install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

```shell
code --install-extension ms-vscode-remote.remote-containers
```

#### DBeaver

Client for Postgres, ClickHouse and other databases. To install, run:

```shell
curl https://dbeaver.io/debs/dbeaver.gpg.key | sudo apt-key add -
echo "deb https://dbeaver.io/debs/dbeaver-ce /" | sudo tee /etc/apt/sources.list.d/dbeaver.list
sudo apt update
sudo apt install dbeaver-ce
```

See the docs for [creating a connection](https://github.com/dbeaver/dbeaver/wiki/Create-Connection).

#### Aliases

Add aliases for frequently used commands to `~/.bash_aliases`:

```shell
# Start warehouse
alias adw="cd /path/to/dw && tilt up --port 29000"

# Stop warehouse
alias sdw="cd /path/to/dw && tilt down"

# Connect to ClickHouse
alias cch="cd /path/to/dw/deploy/clickhouse && docker compose exec clickhouse clickhouse-client --user analyst --password analyst"

# Open shell
alias dwt="cd /path/to/dw/deploy/analytics && docker compose exec cli bash"

# Open VS Code dev container
alias dwc="cd /path/to/dw && ./scripts/open.sh vscode"

# Open Jupyter
alias dwj="cd /path/to/dw && ./scripts/open.sh jupyter"
```

Set `/path/to/` to the location of the repository on your machine.

### Uninstall

1. Start the services, if not already running:

    ```shell
    tilt up --port 29000
    ```

2. For each project that has database syncing, stop PeerDB syncing:

    ```shell
    ./scripts/cli.sh peerdb uninstall <PROJECT_NAME>
    ```

3. Delete all the data and Docker images:

    ```shell
    tilt down
    ./scripts/docker.sh destroy
    ```

## Production

### Install

1. Install [Docker Engine v23 or higher](https://docs.docker.com/engine/install/) and [Docker Compose v2 or higher](https://docs.docker.com/compose/install/). Follow the links for instructions or run this script:

    ```shell
    ./scripts/install.sh docker
    ```

2. Install PeerDB:

    ```shell
    ./scripts/install.sh peerdb
    ```

3. Install a deployment configuration:

    ```shell
    ./scripts/deployment-install.sh <REPOSITORY_URL> <BRANCH_NAME>
    ```

4. For each project, clone its repo:

    ```shell
    cd analytics/projects
    git clone <REPOSITORY_URL> <PROJECT_NAME>
    ```

5. Build the Docker images:

    ```shell
    ./scripts/docker.sh build
    ```

6. Start the services:

    ```shell
    ./scripts/docker.sh up prod
    ```

7. Run the provision script to configure Prefect:

    ```shell
    ./scripts/cli.sh prefect provision dev
    ```

8. For each project, install its dependencies:

    ```shell
    ./scripts/cli.sh project refresh <PROJECT_NAME>
    ```

9. For each project that has database syncing, set up PeerDB and sync the ClickHouse database:

    ```shell
    ./scripts/cli.sh peerdb install <PROJECT_NAME>
    ```

    To check the progress, open [http://localhost:3000/mirrors](http://localhost:3000/mirrors).

### Uninstall

1. Start the services, if not already running:

    ```shell
    ./scripts/docker.sh up prod
    ```

2. For each project that has database syncing, stop PeerDB syncing:

    ```shell
    ./scripts/cli.sh peerdb uninstall <PROJECT_NAME>
    ```

3. Delete all the data and Docker images:

    ```shell
    ./scripts/docker.sh down
    ./scripts/docker.sh destroy
    ```

## Deployment configuration

The deployment configurations of the services are stored in a Git repo that's cloned to `./deploy`. Profiles are stored in branches, e.g. `dev` for development, `prod` for production.

### Prerequisite

Install [uv v0.5.18 or higher](https://docs.astral.sh/uv/getting-started/installation). Follow the link for instructions or run this script:

```shell
./scripts/install.sh uv
```

### Create a configuration

To create a configuration, run:

```shell
./scripts/deployment-create.sh [DESTINATION_DIR]
```

The destination directory is optional and defaults to `./deploy`.

### Install a configuration

To install a configuration, run:

```shell
./scripts/deployment-install.sh <REPOSITORY_URL> <BRANCH_NAME>
```

This command operates on `./deploy`. If the directory doesn't exist, then the given repository is cloned to `./deploy`. Else, the given branch is fetched. The command also creates a Git config file (`./deploy/analytics/.gitconfig`) for the current user that's used inside the CLI and VS Code dev containers.
