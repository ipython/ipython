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
                        .text("Metadata (I know what I'm dooing and I won't complain if it breaks my notebook)")
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
        $(dialogform).dialog({
                autoOpen: true,
                height: 300,
                width: 650,
                modal: true,
                buttons: {
                    "Ok": function() {
                        //validate json and set it
                        try {
                           var json = JSON.parse(editor.getValue());
                           cell.metadata = json;
                           $( this ).dialog( "close" );
                        }
                        catch(e)
                        {
                           error_div.text('Warning, invalid json, not saved');
                        }
                    },
                    Cancel: function() {
                        $( this ).dialog( "close" );
                    }
                },
                close: function() {
                    //cleanup on close
                    $(this).remove();
                }
        });
        editor.refresh();
    }

    var add_raw_edit_button = function(div, cell) {
        var button_container = $(div)
        var button = $('<div/>').button({label:'Raw Edit'})
                .click(function(){raw_edit(cell); return false;})
        button_container.append(button);
    }

    CellToolbar.register_callback('example.rawedit',add_raw_edit_button);
    var example_preset = []
    example_preset.push('example.rawedit');


    var simple_button = function(div, cell) {
        var button_container = $(div);
        var button = $('<div/>').button({icons:{primary:'ui-icon-locked'}});
        var fun = function(value){
                try{
                    if(value){
                        cell.code_mirror.setOption('readOnly','nocursor')
                        button.button('option','icons',{primary:'ui-icon-locked'})
                    } else {
                        cell.code_mirror.setOption('readOnly','false')
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

    var checkbox_test =  function(div, cell) {
        var button_container = $(div)

        var chkb = $('<input/>').attr('type','checkbox');
        var lbl = $('<label/>').append($('<span/>').text('bar :').css('font-size','77%'));
        lbl.append(chkb);
        chkb.attr("checked",cell.metadata.bar);
        chkb.click(function(){
                    var v = cell.metadata.bar;
                    cell.metadata.bar = !v;
                    chkb.attr("checked",!v);
                })
       button_container.append($('<div/>').append(lbl));

    }

    CellToolbar.register_callback('example.checkbox',checkbox_test);
    example_preset.push('example.checkbox');

    var select_test =  function(div, cell) {
        var button_container = $(div)

        var select = $('<select/>');

        select.append($('<option/>').attr('value','foo').text('foo'));
        select.append($('<option/>').attr('value','bar').text('bar'));
        select.append($('<option/>').attr('value','qux').text('qux'));
        select.append($('<option/>').attr('value','zip').text('zip'));
        select.val(cell.metadata.option);
        select.change(function(){
                cell.metadata.option = select.val();
                });
       button_container.append($('<div/>').append(select));

    }

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
