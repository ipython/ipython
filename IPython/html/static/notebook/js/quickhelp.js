// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

//============================================================================
// QuickHelp button
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var platform = IPython.utils.platform;

    var QuickHelp = function (selector) {
    };

    var cmd_ctrl = 'Ctrl-';
    var platform_specific;

    if (platform === 'MacOS') {
        // Mac OS X specific
        cmd_ctrl = 'Cmd-';
        platform_specific = [
            { shortcut: "Cmd-Up",     help:"go to cell start"  },
            { shortcut: "Cmd-Down",   help:"go to cell end"  },
            { shortcut: "Opt-Left",   help:"go one word left"  },
            { shortcut: "Opt-Right",  help:"go one word right"  },
            { shortcut: "Opt-Backspace",      help:"del word before"  },
            { shortcut: "Opt-Delete",         help:"del word after"  },
        ];
    } else {
        // PC specific
        platform_specific = [
            { shortcut: "Ctrl-Home",  help:"go to cell start"  },
            { shortcut: "Ctrl-Up",     help:"go to cell start"  },
            { shortcut: "Ctrl-End",   help:"go to cell end"  },
            { shortcut: "Ctrl-Down",  help:"go to cell end"  },
            { shortcut: "Ctrl-Left",  help:"go one word left"  },
            { shortcut: "Ctrl-Right", help:"go one word right"  },
            { shortcut: "Ctrl-Backspace", help:"del word before"  },
            { shortcut: "Ctrl-Delete",    help:"del word after"  },
        ];
    }

    var cm_shortcuts = [
        { shortcut:"Tab",   help:"code completion or indent" },
        { shortcut:"Shift-Tab",   help:"tooltip" },
        { shortcut: cmd_ctrl + "]",   help:"indent"  },
        { shortcut: cmd_ctrl + "[",   help:"dedent"  },
        { shortcut: cmd_ctrl + "a",   help:"select all"  },
        { shortcut: cmd_ctrl + "z",   help:"undo"  },
        { shortcut: cmd_ctrl + "Shift-z",   help:"redo"  },
        { shortcut: cmd_ctrl + "y",   help:"redo"  },
    ].concat( platform_specific );



      


    QuickHelp.prototype.show_keyboard_shortcuts = function () {
        // toggles display of keyboard shortcut dialog
        var that = this;
        if ( this.force_rebuild ) {
            this.shortcut_dialog.remove();
            delete(this.shortcut_dialog);
            this.force_rebuild = false;
        }
        if ( this.shortcut_dialog ){
            // if dialog is already shown, close it
            $(this.shortcut_dialog).modal("toggle");
            return;
        }
        var command_shortcuts = IPython.keyboard_manager.command_shortcuts.help();
        var edit_shortcuts = IPython.keyboard_manager.edit_shortcuts.help();
        var help, shortcut;
        var i, half, n;
        var element = $('<div/>');

        // The documentation
        var doc = $('<div/>').addClass('alert');
        doc.append(
            $('<button/>').addClass('close').attr('data-dismiss','alert').html('&times;')
        ).append(
            'The IPython Notebook has two different keyboard input modes. <b>Edit mode</b> '+
            'allows you to type code/text into a cell and is indicated by a green cell '+
            'border. <b>Command mode</b> binds the keyboard to notebook level actions '+
            'and is indicated by a grey cell border.'
        );
        element.append(doc);

        // Command mode
        var cmd_div = this.build_command_help();
        element.append(cmd_div);

        // Edit mode
        var edit_div = this.build_edit_help(cm_shortcuts);
        element.append(edit_div);

        this.shortcut_dialog = IPython.dialog.modal({
            title : "Keyboard shortcuts",
            body : element,
            destroy : false,
            buttons : {
                Close : {}
            }
        });
        this.shortcut_dialog.addClass("modal_stretch");
        
        $([IPython.events]).on('rebuild.QuickHelp', function() { that.force_rebuild = true;});
    };

    QuickHelp.prototype.build_command_help = function () {
        var command_shortcuts = IPython.keyboard_manager.command_shortcuts.help();
        return build_div('<h4>Command Mode (press <code>Esc</code> to enable)</h4>', command_shortcuts);
    };

    var special_case = { pageup: "PageUp", pagedown: "Page Down", 'minus': '-' };
    var prettify = function (s) {
        s = s.replace(/-$/, 'minus'); // catch shortcuts using '-' key
        var keys = s.split('-');
        var k, i;
        for (i=0; i < keys.length; i++) {
            k = keys[i];
            if ( k.length == 1 ) {
                keys[i] = "<code><strong>" + k + "</strong></code>";
                continue; // leave individual keys lower-cased
            }
            keys[i] = ( special_case[k] ? special_case[k] : k.charAt(0).toUpperCase() + k.slice(1) );
            keys[i] = "<code><strong>" + keys[i] + "</strong></code>";
        }
        return keys.join('-');


    };

    QuickHelp.prototype.build_edit_help = function (cm_shortcuts) {
        var edit_shortcuts = IPython.keyboard_manager.edit_shortcuts.help();
        jQuery.merge(cm_shortcuts, edit_shortcuts);
        return build_div('<h4>Edit Mode (press <code>Enter</code> to enable)</h4>', cm_shortcuts);
    };

    var build_one = function (s) {
        var help = s.help;
        var shortcut = prettify(s.shortcut);
        return $('<div>').addClass('quickhelp').
            append($('<span/>').addClass('shortcut_key').append($(shortcut))).
            append($('<span/>').addClass('shortcut_descr').text(' : ' + help));

    };

    var build_div = function (title, shortcuts) {
        var i, half, n;
        var div = $('<div/>').append($(title));
        var sub_div = $('<div/>').addClass('hbox');
        var col1 = $('<div/>').addClass('box-flex1');
        var col2 = $('<div/>').addClass('box-flex1');
        n = shortcuts.length;
        half = ~~(n/2);  // Truncate :)
        for (i=0; i<half; i++) { col1.append( build_one(shortcuts[i]) ); }
        for (i=half; i<n; i++) { col2.append( build_one(shortcuts[i]) ); }
        sub_div.append(col1).append(col2);
        div.append(sub_div);
        return div;
    };

    // Set module variables
    IPython.QuickHelp = QuickHelp;

    return IPython;

}(IPython));
