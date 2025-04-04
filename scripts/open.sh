#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

name_choices=("dbt-docs" "jupyter" "prefect-server" "vscode" "cadvisor" "grafana" "prometheus")

if [[ "$1" == "--help" || "$1" == "-h" ]] || [ -z "$1" ]; then
    echo "Usage: $0 NAME"
    echo ""
    echo "Options:"
    echo "    name: ${name_choices[@]}"
    exit 0
fi

name="$1"

if [[ ! "${name_choices[@]}" =~ "${name}" ]]; then
    echo "${tput_red}Invalid name '${name}'. Valid values are: ${name_choices[@]}${tput_reset}"
    exit 1
fi

cd "${root_dir}"

if [ "${name}" == "dbt-docs" ]; then
    source deploy/analytics/.env
    open_cmd "http://localhost:${DW_DBT_DOCS_PORT}"
elif [ "${name}" == "jupyter" ]; then
    source deploy/analytics/.env
    open_cmd "http://localhost:${DW_JUPYTER_PORT}/nbclassic/tree"
elif [ "${name}" == "prefect-server" ]; then
    source deploy/analytics/.env
    open_cmd "http://localhost:${DW_PREFECT_SERVER_PORT}"
elif [ "${name}" == "vscode" ]; then
    cd analytics
    vscode_remote_cmd "$PWD" /home/analyst
elif [ "${name}" == "cadvisor" ]; then
    source deploy/monitor/.env
    open_cmd "http://localhost:${DW_CADVISOR_PORT}"
elif [ "${name}" == "grafana" ]; then
    source deploy/monitor/.env
    open_cmd "http://localhost:${DW_GRAFANA_PORT}"
elif [ "${name}" == "prometheus" ]; then
    source deploy/monitor/.env
    open_cmd "http://localhost:${DW_PROMETHEUS_PORT}"
fi
