//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CellToolbar Example
//============================================================================

/**
 * Example Use for the CellToolbar library
 * add the following to your custom.js to load
 * Celltoolbar UI for slideshow
 *
 * ```
 * $.getScript('/static/js/examples/celltoolbar.example.js');
 * ```
 */
 // IIFE without asignement, we don't modifiy the IPython namespace
(function (IPython) {
    "use strict";

    var CellToolbar = IPython.CellToolbar;

    var simple_button = function(div, cell) {
        var button_container = $(div);
        var button = $('<div/>').button({icons:{primary:'ui-icon-locked'}});
        var fun = function(value){
                try{
                    if(value){
                        cell.code_mirror.setOption('readOnly','nocursor')
                        button.button('option','icons',{primary:'ui-icon-locked'})
                    } else {
                        cell.code_mirror.setOption('readOnly',false)
                        button.button('option','icons',{primary:'ui-icon-unlocked'})
                    }
                } catch(e){}

        }
            fun(cell.metadata.ro)
            button.click(function(){
                    var v = cell.metadata.ro;
                    var locked = !v;
                    cell.metadata.ro = locked;
                    fun(locked)
                    })
                .css('height','16px')
                .css('width','35px');
        button_container.append(button);
    }

    CellToolbar.register_callback('example.lock',simple_button);
    example_preset.push('example.lock');

    var toggle_test =  function(div, cell) {
        var button_container = $(div)
        var button = $('<div/>')
            .button({label:String(cell.metadata.foo)}).
            css('width','65px');
        button.click(function(){
                    var v = cell.metadata.foo;
                    cell.metadata.foo = !v;
                    button.button("option","label",String(!v));
                })
       button_container.append(button);
    }

    CellToolbar.register_callback('example.toggle',toggle_test);
    example_preset.push('example.toggle');

    var checkbox_test = CellToolbar.utils.checkbox_ui_generator('Yes/No',
         // setter
         function(cell, value){
             // we check that the slideshow namespace exist and create it if needed
             if (cell.metadata.yn_test == undefined){cell.metadata.yn_test = {}}
             // set the value
             cell.metadata.yn_test.value = value
             },
         //geter
         function(cell){ var ns = cell.metadata.yn_test;
             // if the slideshow namespace does not exist return `undefined`
             // (will be interpreted as `false` by checkbox) otherwise
             // return the value
             return (ns == undefined)? undefined: ns.value
             }
    );


    CellToolbar.register_callback('example.checkbox',checkbox_test);
    example_preset.push('example.checkbox');

    var select_test = CellToolbar.utils.select_ui_generator([
            ["-"            ,undefined      ],
            ["Header Slide" ,"header_slide" ],
            ["Slide"        ,"slide"        ],
            ["Fragment"     ,"fragment"     ],
            ["Skip"         ,"skip"         ],
            ],
            // setter
            function(cell,value){
                // we check that the slideshow namespace exist and create it if needed
                if (cell.metadata.test == undefined){cell.metadata.test = {}}
                // set the value
                cell.metadata.test.slide_type = value
                },
            //geter
            function(cell){ var ns = cell.metadata.test;
                // if the slideshow namespace does not exist return `undefined`
                // (will be interpreted as `false` by checkbox) otherwise
                // return the value
                return (ns == undefined)? undefined: ns.slide_type
                });

    CellToolbar.register_callback('example.select',select_test);
    example_preset.push('example.select');

    var simple_dialog = function(title,text){
        var dlg = $('<div/>').attr('title',title)
            .append($('<p/>').text(text))
        $(dlg).dialog({
                autoOpen: true,
                height: 300,
                width: 650,
                modal: true,
                close: function() {
                    //cleanup on close
                    $(this).remove();
                }
        });
    }

    var add_simple_dialog_button = function(div, cell) {
        var help_text = ["This is the Metadata editting UI.",
                         "It heavily rely on plugin to work ",
                         "and is still under developpement. You shouldn't wait too long before",
                         " seeing some customisable buttons in those toolbar."
                        ].join('\n')
        var button_container = $(div)
        var button = $('<div/>').button({label:'?'})
                .click(function(){simple_dialog('help',help_text); return false;})
        button_container.append(button);
    }

    CellToolbar.register_callback('example.help',add_simple_dialog_button)
    example_preset.push('example.help')

    CellToolbar.register_preset('example',example_preset);
    console.log('Example extension for metadata editting loaded.');

}(IPython));
