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
        var element = $('<div/>');

        // The documentation
        var doc = $('<div/>').addClass('alert');
        doc.append(
            $('<button/>').addClass('close').attr('data-dismiss','alert').html('&times')
        ).append(
            'The IPython Notebook has two different keyboard input modes. <b>Edit mode</b> '+
            'allow you the type code/text into a cell and is indicated by a green cell '+
            'border. <b>Commmand mode</b> binds the keyboard to notebook level actions '+
            'and is in dicated by a grey cell border.'
        )
        element.append(doc);

        // Command mode
        var cmd_div = $('<div/>').addClass('clearfix').append($('<h4>Command Mode (press ESC to enable)</h4>'));
        element.append(cmd_div);
        for (var i=0; i<command_shortcuts.length; i++) {
            help = command_shortcuts[i]['help'];
            shortcut = command_shortcuts[i]['shortcut'];
            if (help) {
                cmd_div.append($('<div>').addClass('quickhelp').
                    append($('<span/>').addClass('shortcut_key').html(shortcut)).
                    append($('<span/>').addClass('shortcut_descr').html(' : ' + help))
                );
            }
        };

        // Edit mode
        var edit_div = $('<div/>').addClass('clearfix').append($('<h4>Edit Mode (press ENTER to enable)</h4>'));
        element.append(edit_div);
        for (var i=0; i<edit_shortcuts.length; i++) {
            help = edit_shortcuts[i]['help'];
            shortcut = edit_shortcuts[i]['shortcut'];
            if (help) {
                edit_div.append($('<div>').addClass('quickhelp').
                    append($('<span/>').addClass('shortcut_key').html(shortcut)).
                    append($('<span/>').addClass('shortcut_descr').html(' : ' + help))
                );
            }
        };
        
        this.shortcut_dialog = IPython.dialog.modal({
            title : "Keyboard shortcuts",
            body : element,
            destroy : false,
            buttons : {
                Close : {}
            }
        });
    };

    // Set module variables
    IPython.QuickHelp = QuickHelp;

    return IPython;

}(IPython));
