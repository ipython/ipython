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
    # pylab and profile don't need the = and the
    # version without simplifies the special cased completion
    opts=$(ipython ${url} --help-all | grep -E "^-{1,2}[^-]" | sed -e "s/<.*//" -e "s/[^=]$/& /" -e "s/^--pylab=$//" -e "s/^--profile=$/--profile /")
    __ipython_complete_last="$url $var"
    __ipython_complete_last_res="$opts"
}

_ipython()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD - 1]}
    local subcommands="notebook qtconsole console kernel profile locate"
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

    if [[ $mode == "profile" ]]; then
        opts="list create"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    elif [[ ${cur} == -* ]]; then
        if [[ $mode == "notebook" ]]; then
            _ipython_get_flags notebook
            opts=$"${opts} ${baseopts}"
        elif [[ $mode == "qtconsole" ]]; then
            _ipython_get_flags qtconsole
            opts="${opts} ${baseopts}"
        elif [[ $mode == "console" ]]; then
            _ipython_get_flags console
        elif [[ $mode == "kernel" ]]; then
            _ipython_get_flags kernel
            opts="${opts} ${baseopts}"
        elif [[ $mode == "locate" ]]; then
            opts=""
        else
            opts=$baseopts
        fi
        # don't drop the trailing space
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    elif [[ ${prev} == "--pylab"* ]] || [[ ${prev} == "--gui"* ]]; then
        if [ -z "$__ipython_complete_pylab" ]; then
            __ipython_complete_pylab=`cat <<EOF | python -
try:
    import IPython.core.shellapp as mod;
    for k in mod.InteractiveShellApp.pylab.values:
        print "%s " % k
except:
    pass
EOF
        `
        fi
        local IFS=$'\t\n'
        COMPREPLY=( $(compgen -W "${__ipython_complete_pylab}" -- ${cur}) )
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
        if [ -z "$mode" ]; then
            COMPREPLY=( $(compgen -f -W "${subcommands}" -- ${cur}) )
        else
            COMPREPLY=( $(compgen -f -- ${cur}) )
        fi
    fi

}
complete -o default -o nospace -F _ipython ipython
