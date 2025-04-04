#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

_help() {
    echo "Usage: $0 [DESTINATION_DIR]"
    echo ""
    echo "Options:"
    echo "    DESTINATION_DIR: Defaults to 'deploy'."
}

if [ "$1" == "--help" ]; then
    _help
    exit 1
fi

cd "${root_dir}"

template_name="deploy"
template_src_dir="./templates/${template_name}"
deploy_dir="${1:-deploy}"

if [ ! -d "${template_src_dir}" ]; then
    echo "${tput_red}Error: Template '$template_name' not found.${tput_reset}"
    exit 1
fi

if [ -d "${deploy_dir}" ]; then
    echo "${tput_red}Error: Destination directory '$deploy_dir' already exists.${tput_reset}"
    exit 1
fi

uv run copier copy --trust "${template_src_dir}" "${deploy_dir}"

create_gitconfig "${deploy_dir}/analytics/.gitconfig"

echo "${tput_green}Created '${deploy_dir}'${tput_reset}"
