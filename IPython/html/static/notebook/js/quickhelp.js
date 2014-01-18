//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// QuickHelp button
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var QuickHelp = function (selector) {
    };

    QuickHelp.prototype.show_keyboard_shortcuts = function () {
        // toggles display of keyboard shortcut dialog
        var that = this;
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
            'allow you the type code/text into a cell and is indicated by a green cell '+
            'border. <b>Command mode</b> binds the keyboard to notebook level actions '+
            'and is indicated by a grey cell border.'
        )
        element.append(doc);

        // Command mode
        var cmd_div = this.build_command_help();
        element.append(cmd_div);

        // Edit mode
        var edit_div = this.build_edit_help();
        element.append(edit_div);

        this.shortcut_dialog = IPython.dialog.modal({
            title : "Keyboard shortcuts",
            body : element,
            destroy : false,
            buttons : {
                Close : {}
            }
        });
    };

    QuickHelp.prototype.build_command_help = function () {
        var command_shortcuts = IPython.keyboard_manager.command_shortcuts.help();
        var help, shortcut;
        var i, half, n;

        // Command mode
        var cmd_div = $('<div/>').append($('<h4>Command Mode (press ESC to enable)</h4>'));
        var cmd_sub_div = $('<div/>').addClass('hbox');
        var cmd_col1 = $('<div/>').addClass('box-flex0');
        var cmd_col2 = $('<div/>').addClass('box-flex0');
        n = command_shortcuts.length;
        half = ~~(n/2);  // Truncate :)
        for (i=0; i<half; i++) {
            help = command_shortcuts[i]['help'];
            shortcut = command_shortcuts[i]['shortcut'];
            cmd_col1.append($('<div>').addClass('quickhelp').
                append($('<span/>').addClass('shortcut_key').text(shortcut)).
                append($('<span/>').addClass('shortcut_descr').text(' : ' + help))
            );
        };
        for (i=half; i<n; i++) {
            help = command_shortcuts[i]['help'];
            shortcut = command_shortcuts[i]['shortcut'];
            cmd_col2.append($('<div>').addClass('quickhelp').
                append($('<span/>').addClass('shortcut_key').text(shortcut)).
                append($('<span/>').addClass('shortcut_descr').text(' : ' + help))
            );
        };
        cmd_sub_div.append(cmd_col1).append(cmd_col2);
        cmd_div.append(cmd_sub_div);
        return cmd_div;
    }

    QuickHelp.prototype.build_edit_help = function () {
        var edit_shortcuts = IPython.keyboard_manager.edit_shortcuts.help();
        var help, shortcut;
        var i, half, n;

        // Edit mode
        var edit_div = $('<div/>').append($('<h4>Edit Mode (press ENTER to enable)</h4>'));
        var edit_sub_div = $('<div/>').addClass('hbox');
        var edit_col1 = $('<div/>').addClass('box-flex0');
        var edit_col2 = $('<div/>').addClass('box-flex0');
        n = edit_shortcuts.length;
        half = ~~(n/2);  // Truncate :)
        for (i=0; i<half; i++) {
            help = edit_shortcuts[i]['help'];
            shortcut = edit_shortcuts[i]['shortcut'];
            edit_col1.append($('<div>').addClass('quickhelp').
                append($('<span/>').addClass('shortcut_key').text(shortcut)).
                append($('<span/>').addClass('shortcut_descr').text(' : ' + help))
            );
        };
        for (i=half; i<n; i++) {
            help = edit_shortcuts[i]['help'];
            shortcut = edit_shortcuts[i]['shortcut'];
            edit_col2.append($('<div>').addClass('quickhelp').
                append($('<span/>').addClass('shortcut_key').text(shortcut)).
                append($('<span/>').addClass('shortcut_descr').text(' : ' + help))
            );
        };
        edit_sub_div.append(edit_col1).append(edit_col2);
        edit_div.append(edit_sub_div);
        return edit_div;
    }

    // Set module variables
    IPython.QuickHelp = QuickHelp;

    return IPython;

}(IPython));
