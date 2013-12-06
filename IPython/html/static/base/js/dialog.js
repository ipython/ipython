//----------------------------------------------------------------------------
//  Copyright (C) 2013  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Utility for modal dialogs with bootstrap
//============================================================================

IPython.namespace('IPython.dialog');

IPython.dialog = (function (IPython) {
    "use strict";
    
    var modal = function (options) {
        var dialog = $("<div/>").addClass("modal").attr("role", "dialog");
        dialog.append(
            $("<div/>")
                .addClass("modal-header")
                .append($("<button>")
                    .addClass("close")
                    .attr("data-dismiss", "modal")
                    .html("&times;")
                ).append(
                    $("<h3/>").text(options.title || "")
                )
        ).append(
            $("<div/>").addClass("modal-body").append(
                options.body || $("<p/>")
            )
        );
        
        var footer = $("<div/>").addClass("modal-footer");
        
        for (var label in options.buttons) {
            var btn_opts = options.buttons[label];
            var button = $("<button/>")
                .addClass("btn")
                .attr("data-dismiss", "modal")
                .text(label);
            if (btn_opts.click) {
                button.click($.proxy(btn_opts.click, dialog));
            }
            if (btn_opts.class) {
                button.addClass(btn_opts.class);
            }
            footer.append(button);
        }
        dialog.append(footer);
        // hook up on-open event
        dialog.on("shown", function() {
            setTimeout(function() {
                footer.find("button").last().focus();
                if (options.open) {
                    $.proxy(options.open, dialog)();
                }
            }, 0);
        });
        
        // destroy dialog on hide, unless explicitly asked not to
        if (options.destroy === undefined || options.destroy) {
            dialog.on("hidden", function () {
                dialog.remove();
            });
        }
        dialog.on("hidden", function () {
            if (IPython.notebook) {
                var cell = IPython.notebook.get_selected_cell();
                if (cell) cell.select();
                IPython.keyboard_manager.enable();
                IPython.keyboard_manager.command_mode();
            }
        });
        
        if (IPython.keyboard_manager) {
            IPython.keyboard_manager.disable();
        }
        
        return dialog.modal(options);
    };

    var edit_metadata = function (md, callback, name) {
        name = name || "Cell";
        var error_div = $('<div/>').css('color', 'red');
        var message = 
            "Manually edit the JSON below to manipulate the metadata for this " + name + "." +
            " We recommend putting custom metadata attributes in an appropriately named sub-structure," +
            " so they don't conflict with those of others.";

        var textarea = $('<textarea/>')
            .attr('rows', '13')
            .attr('cols', '80')
            .attr('name', 'metadata')
            .text(JSON.stringify(md || {}, null, 2));
        
        var dialogform = $('<div/>').attr('title', 'Edit the metadata')
            .append(
                $('<form/>').append(
                    $('<fieldset/>').append(
                        $('<label/>')
                        .attr('for','metadata')
                        .text(message)
                        )
                        .append(error_div)
                        .append($('<br/>'))
                        .append(textarea)
                    )
            );
        var editor = CodeMirror.fromTextArea(textarea[0], {
            lineNumbers: true,
            matchBrackets: true,
            indentUnit: 2,
            autoIndent: true,
            mode: 'application/json',
        });
        IPython.dialog.modal({
            title: "Edit " + name + " Metadata",
            body: dialogform,
            buttons: {
                OK: { class : "btn-primary",
                    click: function() {
                        // validate json and set it
                        var new_md;
                        try {
                            new_md = JSON.parse(editor.getValue());
                        } catch(e) {
                            console.log(e);
                            error_div.text('WARNING: Could not save invalid JSON.');
                            return false;
                        }
                        callback(new_md);
                    }
                },
                Cancel: {}
            }
        });
        editor.refresh();
    };
    
    return {
        modal : modal,
        edit_metadata : edit_metadata,
    };

}(IPython));
