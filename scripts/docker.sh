#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

dirs=(
    "analytics"
    "clickhouse"
    "monitor"
    "peerdb"
)

help() {
    echo "Usage: $0 <COMMAND>"
    echo ""
    echo "Arguments:"
    echo "    command: down, build, destroy"
    echo ""
    echo ""
    echo "Usage: $0 <COMMAND> <PROFILE>"
    echo ""
    echo "Arguments:"
    echo "    command: up"
    echo "    profile: dev, prod"
}

up() {
    local profile="$1"

    cd "${root_dir}/deploy/clickhouse"
    docker compose up -d

    cd "${root_dir}/deploy/peerdb"
    docker compose up -d

    cd "${root_dir}/deploy/analytics"

    if [ "$profile" == "dev" ]; then
        docker compose up -d prefect-postgres prefect-server prefect-worker cli api jupyter test-clickhouse test-postgres
    else
        docker compose up -d prefect-postgres prefect-server prefect-worker cli api
    fi
}

down() {
    cd "${root_dir}/deploy/analytics"
    docker compose down

    cd "${root_dir}/deploy/peerdb"
    docker compose down

    cd "${root_dir}/deploy/clickhouse"
    docker compose down
}

build() {
    for dir in "${dirs[@]}"; do
        cd "${root_dir}/deploy/${dir}"

        services=$(yq_cmd '.services | to_entries | map(select(.value.build != null) | .key) | .[]' docker-compose.yml)
        for service in $services; do
            cmd="docker compose build ${service} --build-arg DOCKER_UID=$(id -u) --build-arg DOCKER_GID=$(id -g)"
            "$cmd"
        done

        services=$(yq_cmd '.services | to_entries | map(select(.value.build == null) | .key) | .[]' docker-compose.yml)
        for service in $services; do
            cmd="docker compose pull ${service}"
            "$cmd"
        done
    done

    echo "${tput_green}Done!${tput_reset}"
}

destroy() {
    for dir in "${dirs[@]}"; do
        cd "${root_dir}/deploy/${dir}"

        # Delete images, volumes and networks
        docker compose down -v --remove-orphans --rmi local

        # Delete images tagged by Tilt
        services=$(yq_cmd '.services | to_entries | map(select(.value.build != null) | .key) | .[]' docker-compose.yml)
        for service in $services; do
            image_name=$(yq_cmd ".services.${service}.image // \"${service}\"" docker-compose.yml | sed 's/:.*//')
            if [ -n $image_name ]; then
                image_ids=$(docker images --format '{{.ID}}' --filter "reference=${image_name}")
                if [[ -n $image_ids ]]; then
                    docker image rm -f $image_ids
                fi
            fi
        done

        # Delete build cache
        docker builder prune -f
    done

    echo "${tput_green}Done!${tput_reset}"
}

if [[ "$1" == "--help" || "$1" == "-h" ]] || [ -z "$1" ]; then
    help
    exit 0
fi

cmd="$1"
profile="$2"

if [ "$cmd" == "up" ]; then
    if ([ "$profile" == "dev" ] || [ "$profile" == "prod" ]); then
        "$cmd" "$profile"
    else
        echo "${tput_red}Error: Profile must be one of: dev, prod${tput_reset}"
    fi
elif command_exists "$cmd"; then
    "$cmd"
else
    echo "${tput_red}Error: Command must be one of: down, build, destroy${tput_reset}"
fi
