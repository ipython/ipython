//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Keyboard management
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var browser = IPython.utils.browser[0];
    var platform = IPython.utils.platform;

    // Default keyboard shortcuts

    var default_common_shortcuts = {
        'shift' : {
            help    : '',
            help_index : '',
            handler : function (event) {
                // ignore shift keydown
                return true;
            }
        },
        'shift-enter' : {
            help    : 'run cell, select below',
            help_index : 'ba',
            handler : function (event) {
                IPython.notebook.execute_cell_and_select_below();
                return false;
            }
        },
        'ctrl-enter' : {
            help    : 'run cell',
            help_index : 'bb',
            handler : function (event) {
                IPython.notebook.execute_cell();
                return false;
            }
        },
        'alt-enter' : {
            help    : 'run cell, insert below',
            help_index : 'bc',
            handler : function (event) {
                IPython.notebook.execute_cell_and_insert_below();
                return false;
            }
        }
    };

    if (platform === 'MacOS') {
        default_common_shortcuts['cmd-s'] =
            {
                help    : 'save notebook',
                help_index : 'fb',
                handler : function (event) {
                    IPython.notebook.save_checkpoint();
                    event.preventDefault();
                    return false;
                }
            };
    } else {
        default_common_shortcuts['ctrl-s'] =
            {
                help    : 'save notebook',
                help_index : 'fb',
                handler : function (event) {
                    IPython.notebook.save_checkpoint();
                    event.preventDefault();
                    return false;
                }
            };
    }

    // Edit mode defaults

    var default_edit_shortcuts = {
        'esc' : {
            help    : 'command mode',
            help_index : 'aa',
            handler : function (event) {
                IPython.notebook.command_mode();
                return false;
            }
        },
        'ctrl-m' : {
            help    : 'command mode',
            help_index : 'ab',
            handler : function (event) {
                IPython.notebook.command_mode();
                return false;
            }
        },
        'up' : {
            help    : '',
            help_index : '',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                var cell = IPython.notebook.get_cell(index);
                if (cell && cell.at_top() && index !== 0) {
                    event.preventDefault();
                    IPython.notebook.command_mode();
                    IPython.notebook.select_prev();
                    IPython.notebook.edit_mode();
                    var cm = IPython.notebook.get_selected_cell().code_mirror;
                    cm.setCursor(cm.lastLine(), 0);
                    return false;
                } else if (cell) {
                    var cm = cell.code_mirror;
                    var cursor = cm.getCursor();
                    cursor.line -= 1;
                    cm.setCursor(cursor);
                    return false;
                }
            }
        },
        'down' : {
            help    : '',
            help_index : '',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                var cell = IPython.notebook.get_cell(index);
                if (cell.at_bottom() && index !== (IPython.notebook.ncells()-1)) {
                    event.preventDefault();
                    IPython.notebook.command_mode();
                    IPython.notebook.select_next();
                    IPython.notebook.edit_mode();
                    var cm = IPython.notebook.get_selected_cell().code_mirror;
                    cm.setCursor(0, 0);
                    return false;
                } else {
                    var cm = cell.code_mirror;
                    var cursor = cm.getCursor();
                    cursor.line += 1;
                    cm.setCursor(cursor);
                    return false;
                }
            }
        },
        'ctrl-shift--' : {
            help    : 'split cell',
            help_index : 'ea',
            handler : function (event) {
                IPython.notebook.split_cell();
                return false;
            }
        },
        'ctrl-shift-subtract' : {
            help    : '',
            help_index : 'eb',
            handler : function (event) {
                IPython.notebook.split_cell();
                return false;
            }
        },
    };

    // Command mode defaults

    var default_command_shortcuts = {
        'enter' : {
            help    : 'edit mode',
            help_index : 'aa',
            handler : function (event) {
                IPython.notebook.edit_mode();
                return false;
            }
        },
        'up' : {
            help    : 'select previous cell',
            help_index : 'da',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                if (index !== 0 && index !== null) {
                    IPython.notebook.select_prev();
                    IPython.notebook.focus_cell();
                }
                return false;
            }
        },
        'down' : {
            help    : 'select next cell',
            help_index : 'db',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                if (index !== (IPython.notebook.ncells()-1) && index !== null) {
                    IPython.notebook.select_next();
                    IPython.notebook.focus_cell();
                }
                return false;
            }
        },
        'k' : {
            help    : 'select previous cell',
            help_index : 'dc',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                if (index !== 0 && index !== null) {
                    IPython.notebook.select_prev();
                    IPython.notebook.focus_cell();
                }
                return false;
            }
        },
        'j' : {
            help    : 'select next cell',
            help_index : 'dd',
            handler : function (event) {
                var index = IPython.notebook.get_selected_index();
                if (index !== (IPython.notebook.ncells()-1) && index !== null) {
                    IPython.notebook.select_next();
                    IPython.notebook.focus_cell();
                }
                return false;
            }
        },
        'x' : {
            help    : 'cut cell',
            help_index : 'ee',
            handler : function (event) {
                IPython.notebook.cut_cell();
                return false;
            }
        },
        'c' : {
            help    : 'copy cell',
            help_index : 'ef',
            handler : function (event) {
                IPython.notebook.copy_cell();
                return false;
            }
        },
        'shift-v' : {
            help    : 'paste cell above',
            help_index : 'eg',
            handler : function (event) {
                IPython.notebook.paste_cell_above();
                return false;
            }
        },
        'v' : {
            help    : 'paste cell below',
            help_index : 'eh',
            handler : function (event) {
                IPython.notebook.paste_cell_below();
                return false;
            }
        },
        'd' : {
            help    : 'delete cell (press twice)',
            help_index : 'ej',
            count: 2,
            handler : function (event) {
                IPython.notebook.delete_cell();
                return false;
            }
        },
        'a' : {
            help    : 'insert cell above',
            help_index : 'ec',
            handler : function (event) {
                IPython.notebook.insert_cell_above('code');
                IPython.notebook.select_prev();
                IPython.notebook.focus_cell();
                return false;
            }
        },
        'b' : {
            help    : 'insert cell below',
            help_index : 'ed',
            handler : function (event) {
                IPython.notebook.insert_cell_below('code');
                IPython.notebook.select_next();
                IPython.notebook.focus_cell();
                return false;
            }
        },
        'y' : {
            help    : 'to code',
            help_index : 'ca',
            handler : function (event) {
                IPython.notebook.to_code();
                return false;
            }
        },
        'm' : {
            help    : 'to markdown',
            help_index : 'cb',
            handler : function (event) {
                IPython.notebook.to_markdown();
                return false;
            }
        },
        'r' : {
            help    : 'to raw',
            help_index : 'cc',
            handler : function (event) {
                IPython.notebook.to_raw();
                return false;
            }
        },
        '1' : {
            help    : 'to heading 1',
            help_index : 'cd',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 1);
                return false;
            }
        },
        '2' : {
            help    : 'to heading 2',
            help_index : 'ce',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 2);
                return false;
            }
        },
        '3' : {
            help    : 'to heading 3',
            help_index : 'cf',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 3);
                return false;
            }
        },
        '4' : {
            help    : 'to heading 4',
            help_index : 'cg',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 4);
                return false;
            }
        },
        '5' : {
            help    : 'to heading 5',
            help_index : 'ch',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 5);
                return false;
            }
        },
        '6' : {
            help    : 'to heading 6',
            help_index : 'ci',
            handler : function (event) {
                IPython.notebook.to_heading(undefined, 6);
                return false;
            }
        },
        'o' : {
            help    : 'toggle output',
            help_index : 'gb',
            handler : function (event) {
                IPython.notebook.toggle_output();
                return false;
            }
        },
        'shift-o' : {
            help    : 'toggle output scrolling',
            help_index : 'gc',
            handler : function (event) {
                IPython.notebook.toggle_output_scroll();
                return false;
            }
        },
        's' : {
            help    : 'save notebook',
            help_index : 'fa',
            handler : function (event) {
                IPython.notebook.save_checkpoint();
                return false;
            }
        },
        'ctrl-j' : {
            help    : 'move cell down',
            help_index : 'eb',
            handler : function (event) {
                IPython.notebook.move_cell_down();
                return false;
            }
        },
        'ctrl-k' : {
            help    : 'move cell up',
            help_index : 'ea',
            handler : function (event) {
                IPython.notebook.move_cell_up();
                return false;
            }
        },
        'l' : {
            help    : 'toggle line numbers',
            help_index : 'ga',
            handler : function (event) {
                IPython.notebook.cell_toggle_line_numbers();
                return false;
            }
        },
        'i' : {
            help    : 'interrupt kernel (press twice)',
            help_index : 'ha',
            count: 2,
            handler : function (event) {
                IPython.notebook.kernel.interrupt();
                return false;
            }
        },
        '0' : {
            help    : 'restart kernel (press twice)',
            help_index : 'hb',
            count: 2,
            handler : function (event) {
                IPython.notebook.restart_kernel();
                return false;
            }
        },
        'h' : {
            help    : 'keyboard shortcuts',
            help_index : 'ge',
            handler : function (event) {
                IPython.quick_help.show_keyboard_shortcuts();
                return false;
            }
        },
        'z' : {
            help    : 'undo last delete',
            help_index : 'ei',
            handler : function (event) {
                IPython.notebook.undelete_cell();
                return false;
            }
        },
        'shift-m' : {
            help    : 'merge cell below',
            help_index : 'ek',
            handler : function (event) {
                IPython.notebook.merge_cell_below();
                return false;
            }
        },
        'q' : {
            help    : 'close pager',
            help_index : 'gd',
            handler : function (event) {
                IPython.pager.collapse();
                return false;
            }
        },
    };


    // Main keyboard manager for the notebook

    var ShortcutManager = IPython.keyboard.ShortcutManager;
    var keycodes = IPython.keyboard.keycodes;

    var KeyboardManager = function () {
        this.mode = 'command';
        this.enabled = true;
        this.bind_events();
        this.command_shortcuts = new ShortcutManager();
        this.command_shortcuts.add_shortcuts(default_common_shortcuts);
        this.command_shortcuts.add_shortcuts(default_command_shortcuts);
        this.edit_shortcuts = new ShortcutManager();
        this.edit_shortcuts.add_shortcuts(default_common_shortcuts);
        this.edit_shortcuts.add_shortcuts(default_edit_shortcuts);
    };

    KeyboardManager.prototype.bind_events = function () {
        var that = this;
        $(document).keydown(function (event) {
            return that.handle_keydown(event);
        });
    };

    KeyboardManager.prototype.handle_keydown = function (event) {
        var notebook = IPython.notebook;

        if (event.which === keycodes.esc) {
            // Intercept escape at highest level to avoid closing
            // websocket connection with firefox
            event.preventDefault();
        }
        
        if (!this.enabled) {
            if (event.which === keycodes.esc) {
                // ESC
                notebook.command_mode();
                return false;
            }
            return true;
        }
        
        if (this.mode === 'edit') {
            return this.edit_shortcuts.call_handler(event);
        } else if (this.mode === 'command') {
            return this.command_shortcuts.call_handler(event);
        }
        return true;
    };

    KeyboardManager.prototype.edit_mode = function () {
        this.last_mode = this.mode;
        this.mode = 'edit';
    };

    KeyboardManager.prototype.command_mode = function () {
        this.last_mode = this.mode;
        this.mode = 'command';
    };

    KeyboardManager.prototype.enable = function () {
        this.enabled = true;
    };

    KeyboardManager.prototype.disable = function () {
        this.enabled = false;
    };

    KeyboardManager.prototype.register_events = function (e) {
        var that = this;
        var handle_focus = function () {
            that.disable();
        };
        var handle_blur = function () {
            that.enable();
        };
        e.on('focusin', handle_focus);
        e.on('focusout', handle_blur);
        // TODO: Very strange. The focusout event does not seem fire for the 
        // bootstrap textboxes on FF25&26...  This works around that by 
        // registering focus and blur events recursively on all inputs within
        // registered element.
        e.find('input').blur(handle_blur);
        e.on('DOMNodeInserted', function (event) {
            var target = $(event.target);
            if (target.is('input')) {
                target.blur(handle_blur);
            } else {
                target.find('input').blur(handle_blur);    
            }
          });
        // There are times (raw_input) where we remove the element from the DOM before
        // focusout is called. In this case we bind to the remove event of jQueryUI,
        // which gets triggered upon removal, iff it is focused at the time.
        // is_focused must be used to check for the case where an element within
        // the element being removed is focused.
        e.on('remove', function () {
            if (IPython.utils.is_focused(e[0])) {
                that.enable();
            }
        });
    };


    IPython.default_common_shortcuts = default_common_shortcuts;
    IPython.default_edit_shortcuts = default_edit_shortcuts;
    IPython.default_command_shortcuts = default_command_shortcuts;
    IPython.KeyboardManager = KeyboardManager;

    return IPython;

}(IPython));
