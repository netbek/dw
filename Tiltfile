def docker_compose_build(project_name, service, context, deps=None, build_args=None):
    build_arg_str = ""
    if build_args:
        for k, v in build_args.items():
            build_arg_str += "--build-arg {}={} ".format(k, str(v))

    ref = "{}-{}".format(project_name, service)
    cmd = "docker compose build {} {}".format(service, build_arg_str).strip()
    deps = deps or []

    custom_build(ref, tag="latest", dir=context, command=cmd, deps=deps)


analytics_settings(enable=False)
version_settings(constraint=">=0.33.20")

docker_compose("./deploy/clickhouse/docker-compose.yml", project_name="dw-clickhouse")
dc_resource("clickhouse", labels=["clickhouse"], project_name="dw-clickhouse")

docker_compose("./deploy/peerdb/docker-compose.yml", project_name="peerdb")
dc_resource("catalog", labels=["peerdb"], project_name="peerdb")
dc_resource("flow-api", labels=["peerdb"], project_name="peerdb")
dc_resource("flow-snapshot-worker", labels=["peerdb"], project_name="peerdb")
dc_resource("flow-worker", labels=["peerdb"], project_name="peerdb")
dc_resource("minio", labels=["peerdb"], project_name="peerdb")
dc_resource("peerdb-ui", labels=["peerdb"], project_name="peerdb")
dc_resource("peerdb", labels=["peerdb"], project_name="peerdb")
dc_resource("temporal-admin-tools", labels=["peerdb"], project_name="peerdb")
dc_resource("temporal-ui", labels=["peerdb"], project_name="peerdb")
dc_resource("temporal", labels=["peerdb"], project_name="peerdb")

project_name = "dw-analytics"
services = [
    "prefect-server",
    "prefect-worker",
    "cli",
    "jupyter",
    "api",
]

for service in services:
    docker_compose_build(
        project_name=project_name,
        service=service,
        context="./deploy/analytics",
        deps=[
            "./analytics/Dockerfile",
            "./analytics/uv.lock",
        ],
        build_args={
            "DOCKER_UID": "$(id -u)",
            "DOCKER_GID": "$(id -g)",
        },
    )

docker_compose("./deploy/analytics/docker-compose.yml", project_name="dw-analytics")

dc_resource("prefect-postgres", labels=["analytics"], project_name="dw-analytics")
dc_resource("prefect-server", labels=["analytics"], project_name="dw-analytics")
dc_resource("prefect-worker", labels=["analytics"], project_name="dw-analytics")
dc_resource("cli", labels=["analytics"], project_name="dw-analytics")
dc_resource("test-clickhouse", labels=["analytics"], project_name="dw-analytics")
dc_resource("test-postgres", labels=["analytics"], project_name="dw-analytics")
dc_resource("api", labels=["analytics"], project_name="dw-analytics")
dc_resource("jupyter", labels=["analytics"], project_name="dw-analytics")

docker_compose("./deploy/monitor/docker-compose.yml", project_name="dw-monitor")
dc_resource("cadvisor", labels=["monitor"], project_name="dw-monitor")
dc_resource("prometheus", labels=["monitor"], project_name="dw-monitor")
dc_resource("grafana", labels=["monitor"], project_name="dw-monitor")
