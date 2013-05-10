//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
//CellToolbar Example
//============================================================================

/**
 * $.getScript('/static/js/celltoolbarpresets/exportcontrol.js');
 * ```
 * or more generally  
 * ```
 * $.getScript('url to this file');
 * ```
 */
 // IIFE without asignement, we don't modifiy the IPython namespace
(function (IPython) {
    "use strict";

    var CellToolbar = IPython.CellToolbar;
    var autoexporthint_preset = [];

    var select_type = CellToolbar.utils.select_ui_generator([
            ["-"            ,undefined      ],
            ["As-is (default)"        ,"as_is"        ],
            ["Commented"    ,"commented"     ],
            ["Omit"     ,"omit"     ],
            ],
            // setter
            function(cell, value){
                // we check that the auto_export_hint namespace exist and create it if needed
                if (cell.metadata.auto_export_hint == undefined){cell.metadata.auto_export_hint = {}}
                // set the value
                cell.metadata.auto_export_hint.export_type = value
                },
            //geter
            function(cell){ var ns = cell.metadata.auto_export_hint;
                // if the auto_export_hint namespace does not exist return `undefined`
                // (will be interpreted as `false` by checkbox) otherwise
                // return the value
                return (ns == undefined)? undefined: ns.export_type
                },
            "Auto Export Hint");

    CellToolbar.register_callback('auto_export_hint.select',select_type);

    autoexporthint_preset.push('auto_export_hint.select');

    CellToolbar.register_preset('Auto Export Hint',autoexporthint_preset);
    console.log('Auto Export Hint extension for metadata editing loaded.');

}(IPython));
