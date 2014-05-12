// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'notebook/js/celltoolbar',
], function($, celltoolbar) {
    "use strict";


    var CellToolbar = celltoolbar.CellToolbar;
    var slideshow_preset = [];

    var _update_cell = function(cell, old_slide_class) {
        // Remove the old slide DOM class if set.
        if (old_slide_class && old_slide_class != '-') {
            cell.element.removeClass('slideshow-'+old_slide_class);
        }
        // add a DOM class to the cell
        var value = _get_cell_type(cell);
        if (value != '-') { cell.element.addClass('slideshow-'+value); }
    };

    var _get_cell_type = function(cell) {
        var ns = cell.metadata.slideshow;
        // if the slideshow namespace does not exist return `undefined`
        // (will be interpreted as `false` by checkbox) otherwise
        // return the value
        return (ns === undefined)? undefined: ns.slide_type;
    };

    var select_type = CellToolbar.utils.select_ui_generator([
            ["-"            ,"-"            ],
            ["Slide"        ,"slide"        ],
            ["Sub-Slide"    ,"subslide"     ],
            ["Fragment"     ,"fragment"     ],
            ["Skip"         ,"skip"         ],
            ["Notes"        ,"notes"        ],
            ],
            // setter
            function(cell, value){
                // we check that the slideshow namespace exist and create it if needed
                if (cell.metadata.slideshow === undefined){cell.metadata.slideshow = {};}
                // set the value
                var old = cell.metadata.slideshow.slide_type;
                cell.metadata.slideshow.slide_type = value;
                // update the slideshow class set on the cell 
                _update_cell(cell, old);
                },
            //geter
            _get_cell_type,
            "Slide Type");

    var register = function (notebook) {
        CellToolbar.register_callback('slideshow.select',select_type);
        slideshow_preset.push('slideshow.select');

        CellToolbar.register_preset('Slideshow',slideshow_preset, notebook);
        console.log('Slideshow extension for metadata editing loaded.');
    };
    return {'register': register};
});
