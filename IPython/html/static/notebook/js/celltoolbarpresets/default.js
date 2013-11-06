//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CellToolbar Default
//============================================================================

/**
 * Example Use for the CellToolbar library
 */
 // IIFE without asignement, we don't modifiy the IPython namespace
(function (IPython) {
    "use strict";

    var CellToolbar = IPython.CellToolbar;

    var raw_edit = function(cell){
        IPython.dialog.edit_metadata(cell.metadata, function (md) {
            cell.metadata = md;
        });
    };

    var add_raw_edit_button = function(div, cell) {
        var button_container = div;
        var button = $('<button/>')
            .addClass("btn btn-mini")
            .text("Edit Metadata")
            .click( function () {
                raw_edit(cell);
                return false;
            });
        button_container.append(button);
    };

    CellToolbar.register_callback('default.rawedit', add_raw_edit_button);
    var example_preset = [];
    example_preset.push('default.rawedit');

    CellToolbar.register_preset('Edit Metadata', example_preset);
    console.log('Default extension for cell metadata editing loaded.');

}(IPython));
