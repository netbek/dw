#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

echo_help() {
    echo "Usage: $0 <PACKAGE> [PACKAGE ...]"
    echo ""
    echo "Arguments:"
    echo "    package: docker, mkcert, peerdb, tilt, uv"
}

docker_compose_exists() {
    docker compose version &> /dev/null
    return $?
}

install_docker() {
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

    if ! version_gte "docker compose version" "3.0.0"; then
        sudo apt install -y docker-compose-plugin
    fi

    echo "${tput_green}Installed Docker${tput_reset}"
}

install_mkcert() {
    echo "${tput_yellow}Installing mkcert ...${tput_reset}"
    sudo apt install libnss3-tools
    curl -JLO "https://dl.filippo.io/mkcert/v1.4.4?for=linux/amd64"
    chmod +x mkcert-v*-linux-amd64
    sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    echo "${tput_green}Installed mkcert${tput_reset}"
}

install_tilt() {
    echo "${tput_yellow}Installing Tilt ...${tput_reset}"
    curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/v0.33.21/scripts/install.sh | bash
    echo "${tput_green}Installed Tilt${tput_reset}"
}

install_peerdb() {
    echo "${tput_yellow}Installing PeerDB ...${tput_reset}"
    uninstall_peerdb
    git clone https://github.com/PeerDB-io/peerdb --branch v0.22.4
    echo "${tput_green}Installed PeerDB${tput_reset}"
}

uninstall_peerdb() {
    if [ -d peerdb ]; then
        rm -fr peerdb

        # Delete volumes
        docker volume rm peerdb_minio-data peerdb_pgdata
    fi
}

install_uv() {
    echo "${tput_yellow}Installing uv ...${tput_reset}"
    curl -fsSL https://astral.sh/uv/0.5.20/install.sh | sh
    echo "${tput_green}Installed uv${tput_reset}"
}

if ([ "$1" == "--help" ] || [ -z "$1" ]); then
    echo_help
    exit 1
fi

cd "${root_dir}"

for package in "$@"; do
    cmd="install_${package}"
    shift

    if command_exists "$cmd"; then
        $cmd
    else
        echo "${tput_red}Error: Package must be one of: docker, mkcert, peerdb, tilt, uv${tput_reset}"
    fi
done
