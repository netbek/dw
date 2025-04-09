#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

_help() {
    echo "Usage: $0 <PACKAGE> [PACKAGE ...]"
    echo ""
    echo "Arguments:"
    echo "    package: docker, mkcert, tilt, uv"
}

docker_compose_exists() {
    docker compose version &> /dev/null
    return $?
}

_docker_install() {
    echo "${tput_yellow}Installing Docker ...${tput_reset}"

    if ! command_exists "docker" || ! docker_compose_exists; then
        sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo -E apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        sudo apt update
    fi

    if ! version_gte "docker --version" "23.0.0"; then
        sudo apt-cache policy docker-ce
        sudo apt install -y docker-ce
        sudo usermod -aG docker "${USER}" # Enable docker without sudo
    fi

    if ! version_gte "docker compose version" "2.0.0"; then
        sudo apt install -y docker-compose-plugin
    fi

    echo "${tput_green}Installed Docker${tput_reset}"
}

_mkcert_install() {
    echo "${tput_yellow}Installing mkcert ...${tput_reset}"
    sudo apt install libnss3-tools
    curl -JLO "https://dl.filippo.io/mkcert/v1.4.4?for=linux/amd64"
    chmod +x mkcert-v*-linux-amd64
    sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    echo "${tput_green}Installed mkcert${tput_reset}"
}

_tilt_install() {
    echo "${tput_yellow}Installing Tilt ...${tput_reset}"
    curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/v0.33.21/scripts/install.sh | bash
    echo "${tput_green}Installed Tilt${tput_reset}"
}

_uv_install() {
    echo "${tput_yellow}Installing uv ...${tput_reset}"

    if command_exists "uv"; then
        uv self update
    else
        curl -fsSL https://astral.sh/uv/0.6.13/install.sh | sh
    fi

    echo "${tput_green}Installed uv${tput_reset}"
}

if [[ "$1" == "--help" || "$1" == "-h" ]] || [ -z "$1" ]; then
    _help
    exit 0
fi

cd "${root_dir}"

for package in "$@"; do
    cmd="_${package}_install"
    shift

    if command_exists "$cmd"; then
        $cmd
    else
        echo "${tput_red}Error: Package must be one of: docker, mkcert, tilt, uv${tput_reset}"
    fi
done
