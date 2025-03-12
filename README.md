# dw

## Guides

- [Installation](docs/01-install.md)
- [ClickHouse](docs/02-clickhouse.md)
- [PeerDB](docs/03-peerdb.md)
- [Analytics: Projects](docs/04-projects.md)
- [Analytics: dbt](docs/05-dbt.md)
- [Analytics: Jupyter Notebook](docs/06-jupyter.md)
- [Analytics: API](docs/07-api.md)
- [Analytics: Prefect](docs/08-prefect.md)
- [Analytics: Operations](docs/09-operations.md)

## File system

```shell
.
├── analytics
│   ├── .dbt # dbt profiles
│   ├── .devcontainer # VS Code dev container configuration
│   ├── .prefect # Prefect profiles
│   ├── examples
│   │   └── tutorial # Tutorial project
│   ├── package # Supplementary CLI and common utilities
│   ├── projects # Data models, Python tasks, workflows, notebooks and tests
│   ├── templates
│   │   └── project # Template for new projects
│   ├── .bashrc # Shell configuration used in CLI container
│   ├── .gitignore # Git configuration used in CLI container
│   ├── .pre-commit-config.yaml # Pre-commit hooks configuration
│   ├── .sqlfluff # SQL linter configuration used in CLI container
│   ├── .sqlfluffignore # SQL linter configuration used in CLI container
│   ├── .yamllint # YAML linter configuration used in CLI container
│   ├── Dockerfile
│   └── pyproject.toml # Python dependencies and configuration in CLI container
├── deploy # Deployment configuration
├── docs
├── peerdb
└── scripts # Installation scripts
```

## Architecture

```mermaid
graph LR
    subgraph app
        A[app]
    end
    subgraph postgres
        B[postgres<br>port: 5432]
    end
    subgraph dw
        subgraph clickhouse
            C[clickhouse<br>HTTP port: 29200<br>TCP port: 29201]
        end
        subgraph peerdb
            D1[catalog<br>port: 9901]
            D2[temporal<br>port: 7233]
            D3[temporal-admin-tools]
            D4[flow-api<br>port: 8112-8113]
            D5[flow-snapshot-worker]
            D6[flow-worker]
            D7[minio<br>port: 9001-9002]
            D8[peerdb<br>port: 9900]
            D9[peerdb-ui<br>port: 3000]
            D10[temporal-ui<br>port: 8085]
            D9 --> D8
        end
        subgraph analytics
            E1[prefect-postgres<br>port: 29110]
            E2[prefect-server<br>port: 29120]
            E3[prefect-worker]
            E4[jupyter<br>port: 29130]
            E5[api<br>port: 29140]
            E6[cli<br>port: 29150]
            E2 --> E3
            E2 --> E1
            E6 --> E2
        end
        subgraph monitor
            F1[cadvisor<br>port: 29300]
            F2[prometheus<br>port: 29310]
            F3[grafana<br>port: 29320]
            F3 --> F2
            F2 --> F1
        end
    end

    A --> E5
    A --> B
    A --> C
    D8 --> B
    D8 --> C
    F1 --> C
    F1 --> E1
    F1 --> E2
    F1 --> E6
    E3 --> C
    E4 --> C
    E5 --> C
    E6 --> C
```

## License

Copyright (c) 2023 Hein Bekker. Licensed under the GNU Affero General Public License, version 3.
