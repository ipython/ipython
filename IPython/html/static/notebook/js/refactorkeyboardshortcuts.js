var IPython = (function (IPython) {
    // It's really important that the keys exactly match DOM ids of menu items.
    var refactor_common_shortcuts = {
        'run_cell_select_below' : {
            shortcut    : 'shift-enter'
        },
        'run_cell' : {
            shortcut    : 'ctrl-enter'
        },
        'run_cell_insert_below' : {
            shortcut    : 'alt-enter'
        }
    };

    // Edit mode defaults
    var refactor_edit_shortcuts = {
        'split_cell' : {
            shortcut    : 'ctrl-shift--'
        }
    };

    // Command mode defaults
    var refactor_command_shortcuts = {
        'edit_mode' : {
            shortcut    : 'enter',
        },
        'select_previous_cell' : {
            shortcut    : 'up'
        },
        'select_next_cell' : {
            shortcut    : 'down'
        },
        'select_previous_cell' : {
            shortcut   : 'k'
        },
        'select_next_cell' : {
            shortcut    : 'j'
        },
        'cut_cell' : {
            shortcut    : 'x'
        },
        'copy_cell' : {
            shortcut    : 'c'
        },
        'delete_cell' : {
            shortcut    : 'd'
        },
        'insert_cell_above' : {
            shortcut    : 'a'
        },
        'insert_cell_below' : {
            shortcut    : 'b'
        },
        'to_code' : {
            shortcut    : 'y'
        },
        'to_markdown' : {
            shortcut    : 'm'
        },
        'to_raw' : {
            shortcut    : 'r'
        },
        'to_heading1' : {
            shortcut    : '1'
        },
        'to_heading2' : {
            shortcut    : '2'
        },
        'to_heading3' : {
            shortcut    : '3'
        },
        'to_heading4' : {
            shortcut : '4'
        },
        'to_heading5' : {
            shortcut    : '5'
        },
        'to_heading6' : {
            shortcut    : '6'
        },
        'toggle_current_output' : {
            shortcut   : 'o'
        },
        'toggle_current_output_scroll' : {
            shortcut    : 'shift-o'
        },
        'save_notebook' : {
            shortcut    : 's'
        },
        'move_cell_down' : {
            shortcut    : 'ctrl-j'
        },
        'move_cell_up' : {
            shortcut    : 'ctrl-k'
        },
        'toggle_line_numbers' : {
            shortcut    : 'l'
        },
        'int_kernel' : {
            shortcut    : 'i'
        },
        'restart_kernel' : {
            shortcut    : '0'
        },
        'keyboard_shortcuts' : {
            shortcut    : 'h'
        },
        'merge_cell_below' : {
            shortcut   : 'shift-m'
        },
        'close_pager' : {
            shortcut   : 'q'
        }
    };

    IPython.common_shortcuts = refactor_common_shortcuts;
    IPython.edit_shortcuts = refactor_edit_shortcuts;
    IPython.command_shortcuts = refactor_command_shortcuts;
    return IPython;
}(IPython));
