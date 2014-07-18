// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'notebook/js/celltoolbar',
    'base/js/dialog',
], function($, celltoolbar, dialog) {
    "use strict";

    var CellToolbar = celltoolbar.CellToolbar;

    var raw_edit = function(cell){
        dialog.edit_metadata(cell.metadata, function (md) {
            cell.metadata = md;
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

    var register = function (notebook, events) {
        CellToolbar.register_callback('default.rawedit', add_raw_edit_button);
        var example_preset = [];
        example_preset.push('default.rawedit');

        CellToolbar.register_preset('Edit Metadata', example_preset, notebook, events);
        console.log('Default extension for cell metadata editing loaded.');
    };
    return {'register': register};
});
