//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CellToolbar Example
//============================================================================

(function(IPython) {
  "use strict";

  var CellToolbar = IPython.CellToolbar;
  var raw_cell_preset = [];

  var select_type = CellToolbar.utils.select_ui_generator([
    ["None", "-"],
    ["LaTeX", "text/latex"],
    ["restructuredText", "text/restructuredtext"],
    ["HTML", "text/html"],
    ["markdown", "text/markdown"],
    ["Python", "text/python"],
    ["Custom", , "dialog"],

    ],
      // setter
      function(cell, value) {
        if (value === '-') {
          delete cell.metadata.raw_mime;
        } else if (value === 'dialog'){
          // IPython.dialog.modal(
          //   "Set custom raw cell format",
          //   
          //   OK 
          // )
          // 
        } else {
          cell.metadata.raw_mime = value;
        }
      },
      //getter
      function(cell) {
        return cell.metadata.raw_mime || "-";
      },
      // name
      "Raw NBConvert Format",
      // cell_types
      ["raw"]
  );

  CellToolbar.register_callback('raw_cell.select', select_type);

  raw_cell_preset.push('raw_cell.select');

  CellToolbar.register_preset('Raw Cell Format', raw_cell_preset);
  console.log('Raw Cell Format toolbar preset loaded.');

}(IPython));