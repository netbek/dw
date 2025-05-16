#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

source "${scripts_dir}/variables.sh"
source "${scripts_dir}/functions.sh"

help() {
    echo "Usage: $0 <PACKAGE> [PACKAGE ...]"
    echo ""
    echo "Arguments:"
    echo "    package: docker, mkcert, tilt, uv"
}

docker_compose_exists() {
    docker compose version &> /dev/null
    return $?
}

docker_install() {
    echo "${tput_yellow}Installing Docker ...${tput_reset}"

    if ! command_exists "docker" || ! docker_compose_exists; then
        # https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
        sudo apt update
        sudo apt install -y ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
            $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
            sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt update
    fi

    if ! version_gte "docker --version" "23.0.0"; then
        # https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
        sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        # Enable docker without sudo
        sudo usermod -aG docker "${USER}"
    fi

    if ! version_gte "docker compose version" "2.0.0"; then
        # https://docs.docker.com/compose/install/linux/#install-using-the-repository
        sudo apt install -y docker-compose-plugin
    fi

    echo "${tput_green}Installed Docker${tput_reset}"
}

mkcert_install() {
    echo "${tput_yellow}Installing mkcert ...${tput_reset}"
    sudo apt install libnss3-tools
    curl -JLO "https://dl.filippo.io/mkcert/v1.4.4?for=linux/amd64"
    chmod +x mkcert-v*-linux-amd64
    sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    echo "${tput_green}Installed mkcert${tput_reset}"
}

tilt_install() {
    echo "${tput_yellow}Installing Tilt ...${tput_reset}"
    curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/v0.33.21/scripts/install.sh | bash
    echo "${tput_green}Installed Tilt${tput_reset}"
}

uv_install() {
    echo "${tput_yellow}Installing uv ...${tput_reset}"

    if command_exists "uv"; then
        uv self update
    else
        curl -fsSL https://astral.sh/uv/0.6.14/install.sh | sh
    fi

    echo "${tput_green}Installed uv${tput_reset}"
}

if [[ "$1" == "--help" || "$1" == "-h" ]] || [ -z "$1" ]; then
    help
    exit 0
fi

cd "${root_dir}"

for package in "$@"; do
    cmd="${package}_install"
    shift

    if command_exists "$cmd"; then
        $cmd
    else
        echo "${tput_red}Error: Package must be one of: docker, mkcert, tilt, uv${tput_reset}"
    fi
done
