#!/bin/bash
set -e

scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_dir="${scripts_dir}/.."

cd "${root_dir}/deploy/analytics"

docker compose exec cli python -c "from dw_lib.cli.root import app; app()" $@
