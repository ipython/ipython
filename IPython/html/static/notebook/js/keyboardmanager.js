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

    var key   = IPython.utils.keycodes;

    var KeyboardManager = function () {
        this.mode = 'command';
        this.last_mode = 'command';
        this.bind_events();
    };

    KeyboardManager.prototype.bind_events = function () {
        var that = this;
        $(document).keydown(function (event) {
            return that.handle_keydown(event);
        });
    };

    KeyboardManager.prototype.handle_keydown = function (event) {
        var notebook = IPython.notebook;
        
        console.log('keyboard_manager', this.mode, event.keyCode);
        
        if (event.which === key.ESC) {
            // Intercept escape at highest level to avoid closing
            // websocket connection with firefox
            event.preventDefault();
        }
        
        if (this.mode === 'null') {
            return this.handle_null_mode(event);
        }
        
        // Event handlers for both command and edit mode
        if ((event.ctrlKey || event.metaKey) && event.keyCode==83) {
            // Save (CTRL+S) or (Command+S on Mac)
            notebook.save_checkpoint();
            event.preventDefault();
            return false;
        } else if (event.which === key.ESC) {
            // Intercept escape at highest level to avoid closing
            // websocket connection with firefox
            event.preventDefault();
            // Don't return yet to allow edit/command modes to handle
        } else if (event.which === key.SHIFT) {
            // ignore shift keydown
            return true;
        } else if (event.which === key.ENTER && event.shiftKey) {
            notebook.execute_selected_cell('shift');
            return false;
        } else if (event.which === key.ENTER && event.altKey) {
            // Execute code cell, and insert new in place
            notebook.execute_selected_cell('alt');
            return false;
        } else if (event.which === key.ENTER && event.ctrlKey) {
            notebook.execute_selected_cell('ctrl');
            return false;
        }
        
        if (this.mode === 'edit') {
            return this.handle_edit_mode(event);
        } else if (this.mode === 'command' && !(event.ctrlKey || event.altKey || event.metaKey)) {
            return this.handle_command_mode(event);
        }
    }

    KeyboardManager.prototype.handle_null_mode = function (event) {
        return true;
    }


    KeyboardManager.prototype.handle_edit_mode = function (event) {
        var notebook = IPython.notebook;
        
        if (event.which === key.ESC) {
            // ESC
            notebook.command_mode();
            return false;
        } else if (event.which === 77 && event.ctrlKey) {
            // Ctrl-m
            notebook.command_mode();
            return false;
        } else if (event.which === key.UPARROW && !event.shiftKey) {
            var cell = notebook.get_selected_cell();
            if (cell && cell.at_top()) {
                event.preventDefault();
                notebook.command_mode()
                notebook.select_prev();
                notebook.edit_mode();
                return false;
            };
        } else if (event.which === key.DOWNARROW && !event.shiftKey) {
            var cell = notebook.get_selected_cell();
            if (cell && cell.at_bottom()) {
                event.preventDefault();
                notebook.command_mode()
                notebook.select_next();
                notebook.edit_mode();
                return false;
            };
        };
        return true;
    }

    KeyboardManager.prototype.handle_command_mode = function (event) {
        var notebook = IPython.notebook;
        
        if (event.which === key.ENTER && !(event.ctrlKey || event.altKey || event.shiftKey)) {
            // Enter edit mode = ENTER alone
            notebook.edit_mode();
            return false;
        } else if (event.which === key.UPARROW && !event.shiftKey) {
            var index = notebook.get_selected_index();
            if (index !== 0 && index !== null) {
                notebook.select_prev();
                var cell = notebook.get_selected_cell();
                cell.focus_cell();
            };
            return false;
        } else if (event.which === key.DOWNARROW && !event.shiftKey) {
            var index = notebook.get_selected_index();
            if (index !== (notebook.ncells()-1) && index !== null) {
                notebook.select_next();
                var cell = notebook.get_selected_cell();
                cell.focus_cell();
            };
            return false;
        } else if (event.which === 88) {
            // Cut selected cell = x
            notebook.cut_cell();
            return false;
        } else if (event.which === 67) {
            // Copy selected cell = c
            notebook.copy_cell();
            return false;
        } else if (event.which === 86) {
            // Paste below selected cell = v
            notebook.paste_cell_below();
            return false;
        } else if (event.which === 68) {
            // Delete selected cell = d
            notebook.delete_cell();
            return false;
        } else if (event.which === 65) {
            // Insert code cell above selected = a
            notebook.insert_cell_above('code');
            notebook.select_prev();
            return false;
        } else if (event.which === 66) {
            // Insert code cell below selected = b
            notebook.insert_cell_below('code');
            notebook.select_next();
            return false;
        } else if (event.which === 89) {
            // To code = y
            notebook.to_code();
            return false;
        } else if (event.which === 77) {
            // To markdown = m
            notebook.to_markdown();
            return false;
        } else if (event.which === 84) {
            // To Raw = t
            notebook.to_raw();
            return false;
        } else if (event.which === 49) {
            // To Heading 1 = 1
            notebook.to_heading(undefined, 1);
            return false;
        } else if (event.which === 50) {
            // To Heading 2 = 2
            notebook.to_heading(undefined, 2);
            return false;
        } else if (event.which === 51) {
            // To Heading 3 = 3
            notebook.to_heading(undefined, 3);
            return false;
        } else if (event.which === 52) {
            // To Heading 4 = 4
            notebook.to_heading(undefined, 4);
            return false;
        } else if (event.which === 53) {
            // To Heading 5 = 5
            notebook.to_heading(undefined, 5);
            return false;
        } else if (event.which === 54) {
            // To Heading 6 = 6
            notebook.to_heading(undefined, 6);
            return false;
        } else if (event.which === 79) {
            // Toggle output = o
            if (event.shiftKey) {
                notebook.toggle_output_scroll();
            } else {
                notebook.toggle_output();
            };
            return false;
        } else if (event.which === 83) {
            // Save notebook = s
            notebook.save_checkpoint();
            return false;
        } else if (event.which === 74) {
            // Move cell down = j
            notebook.move_cell_down();
            return false;
        } else if (event.which === 75) {
            // Move cell up = k
            notebook.move_cell_up();
            return false;
        } else if (event.which === 80) {
            // Select previous = p
            notebook.select_prev();
            return false;
        } else if (event.which === 78) {
            // Select next = n
            notebook.select_next();
            return false;
        } else if (event.which === 76) {
            // Toggle line numbers = l
            notebook.cell_toggle_line_numbers();
            return false;
        } else if (event.which === 73) {
            // Interrupt kernel = i
            notebook.kernel.interrupt();
            return false;
        } else if (event.which === 190) {
            // Restart kernel = .  # matches qt console
            notebook.restart_kernel();
            return false;
        } else if (event.which === 72) {
            // Show keyboard shortcuts = h
            IPython.quick_help.show_keyboard_shortcuts();
            return false;
        } else if (event.which === 90) {
            // Undo last cell delete = z
            notebook.undelete();
            return false;
        };
        // If we havn't handled it, let someone else.
        return true;
    };

    KeyboardManager.prototype.edit_mode = function () {
        console.log('KeyboardManager', 'changing to edit mode');
        this.last_mode = this.mode;
        this.mode = 'edit';
    }

    KeyboardManager.prototype.command_mode = function () {
        console.log('KeyboardManager', 'changing to command mode');
        this.last_mode = this.mode;
        this.mode = 'command';
    }

    KeyboardManager.prototype.null_mode = function () {
        console.log('KeyboardManager', 'changing to null mode');
        this.last_mode = this.mode;
        this.mode = 'null';
    }

    KeyboardManager.prototype.last_mode = function () {
        var lm = this.last_mode;
        this.last_mode = this.mode;
        this.mode = lm;
    }


    IPython.KeyboardManager = KeyboardManager;

    return IPython;

}(IPython));
