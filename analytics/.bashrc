if [ -f /etc/bash_completion ]; then
    source /etc/bash_completion
fi

if [ -f /usr/local/dbt/dbt-completion.bash ]; then
    source /usr/local/dbt/dbt-completion.bash
fi

ansi_reset="\[\033[0m\]"
ansi_green="\[\033[1;32m\]"
ansi_yellow="\[\033[1;38;5;226m\]"
ansi_cyan="\[\033[1;36m\]"

tput_red=`tput setaf 1`
tput_green=`tput setaf 2`
tput_yellow=`tput setaf 3`
tput_reset=`tput sgr0`

PS1="${ansi_green}\u${ansi_reset}:${ansi_cyan}\w${ansi_reset}\$ "

# Prevent bash and less history files from being stored.
export HISTFILE=/dev/null
export LESSHISTFILE=/dev/null

# Check whether the 2nd directory is a descendant of the 1st directory.
function is_subdirectory() {
    local parent_dir=$(realpath "$1")
    local child_dir=$(realpath "$2")

    if [[ "$child_dir" == "$parent_dir"* ]] && [[ "$child_dir" != "$parent_dir" ]]; then
        return 0
    else
        return 1
    fi
}

# Parse the project name from the given path.
function get_project_name_from_path() {
    if is_subdirectory "$1" "$2"; then
        echo "${2#$1}" | cut -d '/' -f2
    fi
}

function clean() {
    echo "${tput_yellow}Cleaning ...${tput_reset}"

    cd "${HOME}"

    local dirs=(
        .cache
        .ipynb_checkpoints
        .local
        .pytest_cache
        .ssh
        __pycache__
    )

    local files=(
        .bash_history
        .bash_logout
        .python_history
        # .prefect/flows.json
        # .prefect/memo_store.toml
    )

    for dir in "${dirs[@]}"; do
        find . -type d -name "$dir" -exec rm -r {} +
    done

    for file in "${files[@]}"; do
        find . -type f -name "$file" -exec rm {} +
    done

    echo "${tput_green}Cleaned${tput_reset}"
}

# Intercept `dbt` calls and ensure that they are executed in the dbt root directory.
# This is useful because dbt behaves best this way, e.g. because dbt can be executed in
# subdirectories and the `dbt_packages` directory is created in the current working directory,
# it could create the `dbt_packages` directory in undesirable locations.
function dbt() {
    if [ ! -z "$1" ] && [[ ! "$1" == -* ]]; then
        local project_name=$(get_project_name_from_path "$PROJECTS_DIR" "$PWD")

        if [ -z "$project_name" ]; then
            echo "${tput_red}Run the dbt command from the project's dbt directory${tput_reset}"
        else
            cd "${PROJECTS_DIR}/${project_name}/dbt" && /opt/venv/bin/dbt "$@"
        fi
    else
        /opt/venv/bin/dbt "$@"
    fi
}

# Intercept `prefect` calls and ensure that they are executed in the project root directory.
# This is useful because, for most commands, Prefect searches for a prefect.yaml and sometimes fails
# silently when it can't find the file, i.e. fails for a non-obvious reason.
function prefect() {
    if [ ! -z "$1" ] && [[ ! "$1" == -* ]]; then
        local project_name=$(get_project_name_from_path "$PROJECTS_DIR" "$PWD")

        if [ -z "$project_name" ]; then
            echo "${tput_red}Run the prefect command from the project's root directory${tput_reset}"
        else
            cd "${PROJECTS_DIR}/${project_name}" && /opt/venv/bin/prefect "$@"
        fi
    else
        /opt/venv/bin/prefect "$@"
    fi
}

alias ls="ls --color=auto"
alias grep="grep --color=auto"
alias fgrep="fgrep --color=auto"
alias egrep="egrep --color=auto"

alias ll="ls -alF"
alias la="ls -A"
alias l="ls -CF"

alias cli="python -c 'from dw_lib.cli.root import app; app()'"
alias pc="pre-commit run --config ${HOME}/.pre-commit-config.yaml --all-files"
