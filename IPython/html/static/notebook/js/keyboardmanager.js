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

    // Setup global keycodes and inverse keycodes.

    // See http://unixpapa.com/js/key.html for a complete description. The short of
    // it is that there are different keycode sets. Firefox uses the "Mozilla keycodes"
    // and Webkit/IE use the "IE keycodes". These keycode sets are mostly the same
    // but have minor differences.

    // These apply to Firefox, (Webkit and IE)
    var _keycodes = {
        'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71, 'h': 72, 'i': 73,
        'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79, 'p': 80, 'q': 81, 'r': 82,
        's': 83, 't': 84, 'u': 85, 'v': 86, 'w': 87, 'x': 88, 'y': 89, 'z': 90,
        '1 !': 49, '2 @': 50, '3 #': 51, '4 $': 52, '5 %': 53, '6 ^': 54,
        '7 &': 55, '8 *': 56, '9 (': 57, '0 )': 48, 
        '[ {': 219, '] }': 221, '` ~': 192,  ', <': 188, '. >': 190, '/ ?': 191,
        '\\ |': 220, '\' "': 222,
        'numpad0': 96, 'numpad1': 97, 'numpad2': 98, 'numpad3': 99, 'numpad4': 100,
        'numpad5': 101, 'numpad6': 102, 'numpad7': 103, 'numpad8': 104, 'numpad9': 105,
        'multiply': 106, 'add': 107, 'subtract': 109, 'decimal': 110, 'divide': 111,
        'f1': 112, 'f2': 113, 'f3': 114, 'f4': 115, 'f5': 116, 'f6': 117, 'f7': 118,
        'f8': 119, 'f9': 120, 'f11': 122, 'f12': 123, 'f13': 124, 'f14': 125, 'f15': 126,
        'backspace': 8, 'tab': 9, 'enter': 13, 'shift': 16, 'ctrl': 17, 'alt': 18,
        'meta': 91, 'capslock': 20, 'esc': 27, 'space': 32, 'pageup': 33, 'pagedown': 34,
        'end': 35, 'home': 36, 'left': 37, 'up': 38, 'right': 39, 'down': 40,
        'insert': 45, 'delete': 46, 'numlock': 144,
    };
    
    // These apply to Firefox and Opera
    var _mozilla_keycodes = {
        '; :': 59, '= +': 61, '- _': 173, 'meta': 224
    }
    
    // This apply to Webkit and IE
    var _ie_keycodes = {
        '; :': 186, '= +': 187, '- _': 189, 
    }
    
    var browser = IPython.utils.browser[0];
    var platform = IPython.utils.platform;
    
    if (browser === 'Firefox' || browser === 'Opera') {
        $.extend(_keycodes, _mozilla_keycodes);
    } else if (browser === 'Safari' || browser === 'Chrome' || browser === 'MSIE') {
        $.extend(_keycodes, _ie_keycodes);
    }

    var keycodes = {};
    var inv_keycodes = {};
    for (var name in _keycodes) {
        var names = name.split(' ');
        if (names.length === 1) {
            var n = names[0]
            keycodes[n] = _keycodes[n]
            inv_keycodes[_keycodes[n]] = n
        } else {
            var primary = names[0];
            var secondary = names[1];
            keycodes[primary] = _keycodes[name]
            keycodes[secondary] = _keycodes[name]
            inv_keycodes[_keycodes[name]] = primary
        }
    }


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
        'shift+enter' : {
            help    : 'run cell, select below',
            help_index : 'ba',
            handler : function (event) {
                IPython.notebook.execute_cell_and_select_below();
                return false;
            }
        },
        'ctrl+enter' : {
            help    : 'run cell',
            help_index : 'bb',
            handler : function (event) {
                IPython.notebook.execute_cell();
                return false;
            }
        },
        'alt+enter' : {
            help    : 'run cell, insert below',
            help_index : 'bc',
            handler : function (event) {
                IPython.notebook.execute_cell_and_insert_below();
                return false;
            }
        }
    }

    if (platform === 'MacOS') {
        default_common_shortcuts['cmd+s'] =
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
        default_common_shortcuts['ctrl+s'] =
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
                IPython.notebook.focus_cell();
                return false;
            }
        },
        'ctrl+m' : {
            help    : 'command mode',
            help_index : 'ab',
            handler : function (event) {
                IPython.notebook.command_mode();
                IPython.notebook.focus_cell();
                return false;
            }
        },
        'up' : {
            help    : '',
            help_index : '',
            handler : function (event) {
                var cell = IPython.notebook.get_selected_cell();
                if (cell && cell.at_top()) {
                    event.preventDefault();
                    IPython.notebook.command_mode()
                    IPython.notebook.select_prev();
                    IPython.notebook.edit_mode();
                    return false;
                };
            }
        },
        'down' : {
            help    : '',
            help_index : '',
            handler : function (event) {
                var cell = IPython.notebook.get_selected_cell();
                if (cell && cell.at_bottom()) {
                    event.preventDefault();
                    IPython.notebook.command_mode()
                    IPython.notebook.select_next();
                    IPython.notebook.edit_mode();
                    return false;
                };
            }
        },
        'alt+-' : {
            help    : 'split cell',
            help_index : 'ea',
            handler : function (event) {
                IPython.notebook.split_cell();
                return false;
            }
        },
        'alt+subtract' : {
            help    : '',
            help_index : 'eb',
            handler : function (event) {
                IPython.notebook.split_cell();
                return false;
            }
        },
        'tab' : {
            help    : 'indent or complete',
            help_index : 'ec',
        },
        'shift+tab' : {
            help    : 'tooltip',
            help_index : 'ed',
        },
    }

    if (platform === 'MacOS') {
        default_edit_shortcuts['cmd+/'] =
            {
                help    : 'toggle comment',
                help_index : 'ee'
            };
        default_edit_shortcuts['cmd+]'] =
            {
                help    : 'indent',
                help_index : 'ef'
            };
        default_edit_shortcuts['cmd+['] =
            {
                help    : 'dedent',
                help_index : 'eg'
            };
    } else {
        default_edit_shortcuts['ctrl+/'] =
            {
                help    : 'toggle comment',
                help_index : 'ee'
            };
        default_edit_shortcuts['ctrl+]'] =
            {
                help    : 'indent',
                help_index : 'ef'
            };
        default_edit_shortcuts['ctrl+['] =
            {
                help    : 'dedent',
                help_index : 'eg'
            };
    }

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
                    var cell = IPython.notebook.get_selected_cell();
                    cell.focus_cell();
                };
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
                    var cell = IPython.notebook.get_selected_cell();
                    cell.focus_cell();
                };
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
                    var cell = IPython.notebook.get_selected_cell();
                    cell.focus_cell();
                };
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
                    var cell = IPython.notebook.get_selected_cell();
                    cell.focus_cell();
                };
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
        'shift+v' : {
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
        'shift+o' : {
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
        'ctrl+j' : {
            help    : 'move cell down',
            help_index : 'eb',
            handler : function (event) {
                IPython.notebook.move_cell_down();
                return false;
            }
        },
        'ctrl+k' : {
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
        'shift+m' : {
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
    }


    // Shortcut manager class

    var ShortcutManager = function (delay) {
        this._shortcuts = {}
        this._counts = {}
        this._timers = {}
        this.delay = delay || 800; // delay in milliseconds
    }

    ShortcutManager.prototype.help = function () {
        var help = [];
        for (var shortcut in this._shortcuts) {
            var help_string = this._shortcuts[shortcut]['help'];
            var help_index = this._shortcuts[shortcut]['help_index'];
            if (help_string) {
                if (platform === 'MacOS') {
                    shortcut = shortcut.replace('meta', 'cmd');
                }
                help.push({
                    shortcut: shortcut,
                    help: help_string,
                    help_index: help_index}
                );
            }
        }
        help.sort(function (a, b) {
            if (a.help_index > b.help_index)
                return 1;
            if (a.help_index < b.help_index)
                return -1;
            return 0;
        });
        return help;
    }

    ShortcutManager.prototype.normalize_key = function (key) {
        return inv_keycodes[keycodes[key]];
    }

    ShortcutManager.prototype.normalize_shortcut = function (shortcut) {
        // Sort a sequence of + separated modifiers into the order alt+ctrl+meta+shift
        shortcut = shortcut.replace('cmd', 'meta').toLowerCase();
        var values = shortcut.split("+");
        if (values.length === 1) {
            return this.normalize_key(values[0])
        } else {
            var modifiers = values.slice(0,-1);
            var key = this.normalize_key(values[values.length-1]);
            modifiers.sort();
            return modifiers.join('+') + '+' + key;
        }
    }

    ShortcutManager.prototype.event_to_shortcut = function (event) {
        // Convert a jQuery keyboard event to a strong based keyboard shortcut
        var shortcut = '';
        var key = inv_keycodes[event.which]
        if (event.altKey && key !== 'alt') {shortcut += 'alt+';}
        if (event.ctrlKey && key !== 'ctrl') {shortcut += 'ctrl+';}
        if (event.metaKey && key !== 'meta') {shortcut += 'meta+';}
        if (event.shiftKey && key !== 'shift') {shortcut += 'shift+';}
        shortcut += key;
        return shortcut
    }

    ShortcutManager.prototype.clear_shortcuts = function () {
        this._shortcuts = {};
    }

    ShortcutManager.prototype.add_shortcut = function (shortcut, data) {
        if (typeof(data) === 'function') {
            data = {help: '', help_index: '', handler: data}
        }
        data.help_index = data.help_index || '';
        data.help = data.help || '';
        data.count = data.count || 1;
        if (data.help_index === '') {
            data.help_index = 'zz';
        }
        shortcut = this.normalize_shortcut(shortcut);
        this._counts[shortcut] = 0;
        this._shortcuts[shortcut] = data;
    }

    ShortcutManager.prototype.add_shortcuts = function (data) {
        for (var shortcut in data) {
            this.add_shortcut(shortcut, data[shortcut]);
        }
    }

    ShortcutManager.prototype.remove_shortcut = function (shortcut) {
        shortcut = this.normalize_shortcut(shortcut);
        delete this._counts[shortcut];
        delete this._shortcuts[shortcut];
    }

    ShortcutManager.prototype.count_handler = function (shortcut, event, data) {
        var that = this;
        var c = this._counts;
        var t = this._timers;
        var timer = null;
        if (c[shortcut] === data.count-1) {
            c[shortcut] = 0;
            var timer = t[shortcut];
            if (timer) {clearTimeout(timer); delete t[shortcut];}
            return data.handler(event);
        } else {
            c[shortcut] = c[shortcut] + 1;
            timer = setTimeout(function () {
                c[shortcut] = 0;
            }, that.delay);
            t[shortcut] = timer;
        }
        return false;
    }

    ShortcutManager.prototype.call_handler = function (event) {
        var shortcut = this.event_to_shortcut(event);
        var data = this._shortcuts[shortcut];
        if (data) {
            var handler = data['handler'];
            if (handler) {
                if (data.count === 1) {
                    return handler(event);
                } else if (data.count > 1) {
                    return this.count_handler(shortcut, event, data);
                }
            }
        }
        return true;
    }



    // Main keyboard manager for the notebook

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

        if (event.which === keycodes['esc']) {
            // Intercept escape at highest level to avoid closing
            // websocket connection with firefox
            event.preventDefault();
        }
        
        if (!this.enabled) {
            if (event.which === keycodes['esc']) {
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
    }

    KeyboardManager.prototype.edit_mode = function () {
        this.last_mode = this.mode;
        this.mode = 'edit';
    }

    KeyboardManager.prototype.command_mode = function () {
        this.last_mode = this.mode;
        this.mode = 'command';
    }

    KeyboardManager.prototype.enable = function () {
        this.enabled = true;
    }

    KeyboardManager.prototype.disable = function () {
        this.enabled = false;
    }

    KeyboardManager.prototype.register_events = function (e) {
        var that = this;
        e.on('focusin', function () {
            that.disable();
        });
        e.on('focusout', function () {
            that.enable();
        });
        // There are times (raw_input) where we remove the element from the DOM before
        // focusout is called. In this case we bind to the remove event of jQueryUI,
        // which gets triggered upon removal, iff it is focused at the time.
        e.on('remove', function () {
            if (document.activeElement === e[0]) {
                that.enable();
            }
        });
    }


    IPython.keycodes = keycodes;
    IPython.inv_keycodes = inv_keycodes;
    IPython.default_common_shortcuts = default_common_shortcuts;
    IPython.default_edit_shortcuts = default_edit_shortcuts;
    IPython.default_command_shortcuts = default_command_shortcuts;
    IPython.ShortcutManager = ShortcutManager;
    IPython.KeyboardManager = KeyboardManager;

    return IPython;

}(IPython));
