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

        var md = cell.metadata
        var error_div = $('<div/>').css('color','red')

        var textarea = $('<textarea/>')
            .attr('rows','13')
            .attr('cols','75')
            .attr('name','metadata')
            .text(JSON.stringify(md, null,4)||'');
        var dialogform = $('<div/>').attr('title','Edit the metadata')
            .append(
                $('<form/>').append(
                    $('<fieldset/>').append(
                        $('<label/>')
                        .attr('for','metadata')
                        .text("Manually edit the JSON below to manipulate the metadata for this cell. This assumes you know what you are doing and won't complain if it breaks your notebook. We also recommend putting your metadata attributes in an appropriately named sub-structure, so they don't conflict with those of others.")
                        )
                        .append(error_div)
                        .append($('<br/>'))
                        .append(
                            textarea
                        )
                    )
            );
        var editor = CodeMirror.fromTextArea(textarea[0], {
            lineNumbers: true,
            matchBrackets: true,
        });
        IPython.dialog.modal({
            title: "Edit Cell Metadata",
            body: dialogform,
                buttons: {
                    "OK": { class : "btn-primary",
                        click: function() {
                        //validate json and set it
                        try {
                           var json = JSON.parse(editor.getValue());
                           cell.metadata = json;
                        } catch(e) {
                           error_div.text('Warning, invalid json, not saved');
                           return false;
                        }
                    }},
                    Cancel: {}
                }
        });
        editor.refresh();
    }

    var add_raw_edit_button = function(div, cell) {
        var button_container = div;
        var button = $('<button/>')
            .addClass("btn btn-mini")
            .text("Raw Edit")
            .click( function () {
                raw_edit(cell);
                return false;
            });
        button_container.append(button);
    }

    CellToolbar.register_callback('default.rawedit',add_raw_edit_button);
    var example_preset = []
    example_preset.push('default.rawedit');

    CellToolbar.register_preset('Default',example_preset);
    console.log('Default extension for metadata editing loaded.');

}(IPython));
