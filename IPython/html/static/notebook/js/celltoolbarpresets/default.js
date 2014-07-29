// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'notebook/js/celltoolbar',
    'base/js/dialog',
], function($, celltoolbar, dialog) {
    "use strict";

    var CellToolbar = celltoolbar.CellToolbar;

    var raw_edit = function (cell) {
        dialog.edit_metadata({
            md: cell.metadata,
            callback: function (md) {
                cell.metadata = md;
            },
            name: 'Cell',
            notebook: this.notebook,
            keyboard_manager: this.keyboard_manager
        });
    };

    var add_raw_edit_button = function(div, cell) {
        var button_container = $(div);
        var button = $('<button/>')
            .addClass("btn btn-default btn-xs")
            .text("Edit Metadata")
            .click( function () {
                raw_edit(cell);
                return false;
            });
        button_container.append(button);
    };

    var register = function (notebook) {
        CellToolbar.register_callback('default.rawedit', add_raw_edit_button);
        raw_edit = $.proxy(raw_edit, {
            notebook: notebook,
            keyboard_manager: notebook.keyboard_manager
        });

        var example_preset = [];
        example_preset.push('default.rawedit');

        CellToolbar.register_preset('Edit Metadata', example_preset, notebook);
        console.log('Default extension for cell metadata editing loaded.');
    };
    return {'register': register};
});
