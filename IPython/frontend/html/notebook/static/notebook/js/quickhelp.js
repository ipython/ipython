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
        var body = $('<div/>');
        var shortcuts = [
            {key: 'Shift-Enter', help: 'run cell'},
            {key: 'Ctrl-Enter', help: 'run cell in-place'},
            {key: 'Alt-Enter', help: 'run cell, insert below'},
            {key: 'Ctrl-m x', help: 'cut cell'},
            {key: 'Ctrl-m c', help: 'copy cell'},
            {key: 'Ctrl-m v', help: 'paste cell'},
            {key: 'Ctrl-m d', help: 'delete cell'},
            {key: 'Ctrl-m z', help: 'undo last cell deletion'},
            {key: 'Ctrl-m a', help: 'insert cell above'},
            {key: 'Ctrl-m b', help: 'insert cell below'},
            {key: 'Ctrl-m o', help: 'toggle output'},
            {key: 'Ctrl-m O', help: 'toggle output scroll'},
            {key: 'Ctrl-m l', help: 'toggle line numbers'},
            {key: 'Ctrl-m s', help: 'save notebook'},
            {key: 'Ctrl-m j', help: 'move cell down'},
            {key: 'Ctrl-m k', help: 'move cell up'},
            {key: 'Ctrl-m y', help: 'code cell'},
            {key: 'Ctrl-m m', help: 'markdown cell'},
            {key: 'Ctrl-m t', help: 'raw cell'},
            {key: 'Ctrl-m 1-6', help: 'heading 1-6 cell'},
            {key: 'Ctrl-m p', help: 'select previous'},
            {key: 'Ctrl-m n', help: 'select next'},
            {key: 'Ctrl-m i', help: 'interrupt kernel'},
            {key: 'Ctrl-m .', help: 'restart kernel'},
            {key: 'Ctrl-m h', help: 'show keyboard shortcuts'}
        ];
        for (var i=0; i<shortcuts.length; i++) {
            body.append($('<div>').
                append($('<span/>').addClass('shortcut_key').html(shortcuts[i].key)).
                append($('<span/>').addClass('shortcut_descr').html(' : ' + shortcuts[i].help))
            );
        };
        this.shortcut_dialog = IPython.dialog.modal({
            title : "Keyboard shortcuts",
            body : body,
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
