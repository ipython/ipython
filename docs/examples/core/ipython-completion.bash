# load with: . ipython-completion.bash

_ipython_get_flags()
{
    local url=$1
    local var=$2
    local dash=$3
    if [[ "$url $var" == $__ipython_complete_last ]]; then
        opts=$__ipython_complete_last_res
        return
    fi
    opts=$(cat <<EOF | python -
try:
    import IPython.${url} as mod;
    for k in mod.${var}:
        print "${dash}%s" % k,
except:
    pass
EOF
    )
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
        _ipython_get_flags core.shellapp "shell_flags.keys()" "--"
        __ipython_complete_baseopts="${opts}"
    fi
    local baseopts="$__ipython_complete_baseopts"
    local mode=""
    for i in "${COMP_WORDS[@]}"; do
        [ "$cur" = "$i" ] && break
        if [[ ${subcommands} == *${i}* ]]; then
            mode="$i"
        fi
    done

    if [[ ${cur} == -* ]]; then
        if [[ $mode == "notebook" ]]; then
            _ipython_get_flags frontend.html.notebook.notebookapp notebook_flags "--"
            opts=$"${opts} ${baseopts}"
        elif [[ $mode == "qtconsole" ]]; then
            _ipython_get_flags frontend.qt.console.qtconsoleapp qt_flags "--"
            opts="${opts} ${baseopts}"
        elif [[ $mode == "console" ]]; then
            _ipython_get_flags frontend.terminal.console.app frontend_flags "--"
        elif [[ $mode == "kernel" ]]; then
            _ipython_get_flags zmq.kernelapp "kernel_flags.keys()" "--"
            opts="${opts} ${baseopts}"
        else
            opts=$baseopts
        fi
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    elif [[ ${prev} == "--pylab"* ]] || [[ ${prev} == "--gui"* ]]; then
        _ipython_get_flags core.shellapp InteractiveShellApp.pylab.values
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    else
        if [ -z "$mode" ]; then
            COMPREPLY=( $(compgen -f -W "${subcommands}" -- ${cur}) )
        else
            COMPREPLY=( $(compgen -f -- ${cur}) )
        fi
    fi

}
complete -o default -F _ipython ipython
