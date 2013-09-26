//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
//CellToolbar Example
//============================================================================

 // IIFE without asignement, we don't modifiy the IPython namespace
(function (IPython) {
    "use strict";

    var CellToolbar = IPython.CellToolbar;
    var slideshow_preset = [];

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
                if (cell.metadata.slideshow == undefined){cell.metadata.slideshow = {}}
                // set the value
                cell.metadata.slideshow.slide_type = value
                },
            //geter
            function(cell){ var ns = cell.metadata.slideshow;
                // if the slideshow namespace does not exist return `undefined`
                // (will be interpreted as `false` by checkbox) otherwise
                // return the value
                return (ns == undefined)? undefined: ns.slide_type
                },
            "Slide Type");

    CellToolbar.register_callback('slideshow.select',select_type);

    slideshow_preset.push('slideshow.select');

    CellToolbar.register_preset('Slideshow',slideshow_preset);
    console.log('Slideshow extension for metadata editing loaded.');

}(IPython));
