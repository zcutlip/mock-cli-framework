# In shell, success is exit(0), error is anything else, e.g., exit(1)
# shellcheck shell=sh
SUCCESS=0
FAILURE=1

quit(){
    if [ $# -gt 1 ];
    then
        echo "$1"
        shift
    fi
    exit "$1"
}

branch_is_master_or_main(){
    _branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$_branch" = "master" ] || [ "$_branch" = "main" ];
    then
        return $SUCCESS;
    else
        return $FAILURE;
    fi
}

branch_is_clean(){
    _modified=$(git ls-files -m) || quit "Unable to check for modified files." $?
    if [ -z "$modified" ];
    then
        return $SUCCESS;
    else
        return $FAILURE;
    fi
}

current_version() {
    _version="$(python ./setup.py --version)" || quit "Unable to detect package version" $?
    printf "%s" "$_version"
}

version_is_tagged(){
    _version="$1"
    # e.g., verion = 0.1.0
    # check if git tag -l v0.1.0 exists
    tag_description=$(git tag -l v"$_version")
    if [ -n "$tag_description" ];
    then
        return $SUCCESS;
    else
        return $FAILURE;
    fi
}

prompt_yes_no(){
    prompt_string="$1"
    read -r -p "$prompt_string [Y/n] " response

    case $response in
    [yY][eE][sS]|[yY])
        return $SUCCESS
        ;;
        *)
        return $FAILURE
        ;;
    esac
}
