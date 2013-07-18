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
        if (options.destroy == undefined || options.destroy) {
            dialog.on("hidden", function () {
                dialog.remove();
            });
        }
        if (options.reselect_cell !== false) {
            dialog.on("hidden", function () {
                if (IPython.notebook) {
                    cell = IPython.notebook.get_selected_cell();
                    if (cell) cell.select();
                }
            });
        }
        
        return dialog.modal(options);
    }
    
    return {
        modal : modal,
    };

}(IPython));
