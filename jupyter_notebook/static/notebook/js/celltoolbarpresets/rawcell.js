// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'notebook/js/celltoolbar',
    'base/js/dialog',
    'base/js/keyboard',
], function($, celltoolbar, dialog, keyboard) {
    "use strict";

  var CellToolbar = celltoolbar.CellToolbar;
  var raw_cell_preset = [];

  var select_type = CellToolbar.utils.select_ui_generator([
    ["None", "-"],
    ["LaTeX", "text/latex"],
    ["reST", "text/restructuredtext"],
    ["HTML", "text/html"],
    ["Markdown", "text/markdown"],
    ["Python", "text/x-python"],
    ["Custom", "dialog"],

    ],
      // setter
      function(cell, value) {
        if (value === "-") {
          delete cell.metadata.raw_mimetype;
        } else if (value === 'dialog'){
            var dialog = $('<div/>').append(
                $("<p/>")
                    .text("Set the MIME type of the raw cell:")
            ).append(
                $("<br/>")
            ).append(
                $('<input/>').attr('type','text').attr('size','25')
                .val(cell.metadata.raw_mimetype || "-")
            );
            dialog.modal({
                title: "Raw Cell MIME Type",
                body: dialog,
                buttons : {
                    "Cancel": {},
                    "OK": {
                        class: "btn-primary",
                        click: function () {
                            console.log(cell);
                            cell.metadata.raw_mimetype = $(this).find('input').val();
                            console.log(cell.metadata);
                        }
                    }
                },
                open : function (event, ui) {
                    var that = $(this);
                    // Upon ENTER, click the OK button.
                    that.find('input[type="text"]').keydown(function (event, ui) {
                        if (event.which === keyboard.keycodes.enter) {
                            that.find('.btn-primary').first().click();
                            return false;
                        }
                    });
                    that.find('input[type="text"]').focus().select();
                }
            });
        } else {
          cell.metadata.raw_mimetype = value;
        }
      },
      //getter
      function(cell) {
        return cell.metadata.raw_mimetype || "";
      },
      // name
      "Raw NBConvert Format"
  );

  var register = function (notebook) {
    CellToolbar.register_callback('raw_cell.select', select_type, ['raw']);
    raw_cell_preset.push('raw_cell.select');

    CellToolbar.register_preset('Raw Cell Format', raw_cell_preset, notebook);
    console.log('Raw Cell Format toolbar preset loaded.');
  };
  return {'register': register};

});
