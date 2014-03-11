# load with: . ipython-completion.bash

if [[ -n ${ZSH_VERSION-} ]]; then
    autoload -Uz bashcompinit && bashcompinit
fi

_ipython_get_flags()
{
    local url=$1
    local var=$2
    local dash=$3
    if [[ "$url $var" == $__ipython_complete_last ]]; then
        opts=$__ipython_complete_last_res
        return
    fi
    # matplotlib and profile don't need the = and the
    # version without simplifies the special cased completion
    opts=$(ipython ${url} --help-all | grep -E "^-{1,2}[^-]" | sed -e "s/<.*//" -e "s/[^=]$/& /" -e "s/^--matplotlib=$//" -e "s/^--profile=$/--profile /")
    __ipython_complete_last="$url $var"
    __ipython_complete_last_res="$opts"
}

_ipython()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD - 1]}
    local subcommands="notebook qtconsole console kernel profile locate history nbconvert "
    local opts=""
    if [ -z "$__ipython_complete_baseopts" ]; then
        _ipython_get_flags baseopts
        __ipython_complete_baseopts="${opts}"
    fi
    local baseopts="$__ipython_complete_baseopts"
    local mode=""
    for i in "${COMP_WORDS[@]}"; do
        [ "$cur" = "$i" ] && break
        if [[ ${subcommands} == *${i}* ]]; then
            mode="$i"
            break
        elif [[ ${i} == "--"* ]]; then
            mode="nosubcommand"
            break
        fi
    done


    if [[ ${cur} == -* ]]; then
        case $mode in
            "notebook" | "qtconsole" | "console" | "kernel" | "nbconvert")
                _ipython_get_flags $mode
                opts=$"${opts} ${baseopts}"
                ;;
            "locate" | "profile")
                _ipython_get_flags $mode
                ;;
            "history")
                if [[ $COMP_CWORD -ge 3 ]]; then
                    # 'history trim' and 'history clear' covered by next line
                    _ipython_get_flags history\ "${COMP_WORDS[2]}"
                else
                    _ipython_get_flags $mode

                fi
                opts=$"${opts}"
                ;;
            *)
                opts=$baseopts
        esac
        # don't drop the trailing space
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    elif [[ $mode == "profile" ]]; then
        opts="list 	create 	locate "
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    elif [[ $mode == "history" ]]; then
        if [[ $COMP_CWORD -ge 3 ]]; then
            # drop into flags
            opts="--"
        else
            opts="trim 	clear "
        fi
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    elif [[ $mode == "locate" ]]; then
        opts="profile"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    elif [[ ${prev} == "--matplotlib"* ]] || [[ ${prev} == "--gui"* ]]; then
        if [ -z "$__ipython_complete_matplotlib" ]; then
            __ipython_complete_matplotlib=`cat <<EOF | python -
try:
    import IPython.core.shellapp as mod;
    for k in mod.InteractiveShellApp.matplotlib.values:
        print "%s " % k
except:
    pass
EOF
        `
        fi
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${__ipython_complete_matplotlib}" -- ${cur}) )
    elif [[ ${prev} == "--profile"* ]]; then
        if [ -z  "$__ipython_complete_profiles" ]; then
        __ipython_complete_profiles=`cat <<EOF | python -
try:
    import IPython.core.profileapp
    for k in IPython.core.profileapp.list_bundled_profiles():
        print "%s " % k
    p = IPython.core.profileapp.ProfileList()
    for k in IPython.core.profileapp.list_profiles_in(p.ipython_dir):
        print "%s " % k
except:
    pass
EOF
        `
        fi
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${__ipython_complete_profiles}" -- ${cur}) )
    else
        if [ "$COMP_CWORD" == 1 ]; then
            local IFS=$'\t\n'
            local sub=$(echo $subcommands | sed -e "s/ / \t/g")
            COMPREPLY=( $(compgen -W "${sub}" -- ${cur}) )
        else
            COMPREPLY=( $(compgen -f -- ${cur}) )
        fi
    fi

}
complete -o default -o nospace -F _ipython ipython
