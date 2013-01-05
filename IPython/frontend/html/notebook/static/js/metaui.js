//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MetaUI
//============================================================================


/**
 * A Module to control the per-cell toolbar.
 * @module IPython
 * @namespace IPython
 * @submodule MetaUI
 */
var IPython = (function (IPython) {
    "use strict";


    /**
     * @constructor
     * @class MetaUI
     * @param {The cell to attach the metadata UI to} cell
     */
    var MetaUI = function (cell) {
        MetaUI._instances.push(this);
        this.metainner = $('<div/>');
        this.cell = cell;
        this.element = $('<div/>').addClass('metaedit')
                .append(this.metainner)
        this.rebuild();
        return this;
    };

    /**
     * Class variable that should contain a dict of all availlable callback
     * we need to think of wether or not we allow nested namespace
     * @property _callback_dict
     * @private
     */
    MetaUI._callback_dict = {};

    /**
     * Class variable that should contain the reverse order list of the button
     * to add to the toolbar of each cell
     * @property _button_list
     * @private
     */
    MetaUI._button_list = [];

    /**
     * keep a list of all instances to
     * be able to llop over them...
     * but how to 'destroy' them ?
     * have to think about it...
     * or loop over the cells, and find their MetaUI instances.
     * @private
     * @property _instances
     */
    MetaUI._instances =[]

    /**
     * keep a list of all the availlabel presets for the toolbar
     * @private
     * @property _presets
     */
    MetaUI._presets ={}

    // this is by design not a prototype.
    /**
     * Register a callback to create an UI element in a cell toolbar.
     * @method register_callback
     * @param name {String} name to use to refer to the callback. It is advised to use a prefix with the name
     * for easier sorting and avoid collision
     * @param  callback {function(div, cell)} callback that will be called to generate the ui element
     *
     *
     * The callback will receive the following element :
     *
     *    * a div in which to add element.
     *    * the cell it is responsable from
     *
     * @example
     *
     * Example that create callback for a button that toggle between `true` and `false` label,
     * with the metadata under the key 'foo' to reflect the status of the button.
     *
     *      // first param reference to a DOM div
     *      // second param reference to the cell.
     *      var toggle =  function(div, cell) {
     *          var button_container = $(div)
     *
     *          // let's create a button that show the  current value of the metadata
     *          var button = $('<div/>').button({label:String(cell.metadata.foo)});
     *
     *          // On click, change the metadata value and update the button label
     *          button.click(function(){
     *                      var v = cell.metadata.foo;
     *                      cell.metadata.foo = !v;
     *                      button.button("option","label",String(!v));
     *                  })
     *
     *          // add the button to the DOM div.
     *          button_container.append(button);
     *      }
     *
     *      // now we register the callback under the name `foo` to give the
     *      // user the ability to use it later
     *      MetaUI.register_callback('foo',toggle);
     */
    MetaUI.register_callback = function(name, callback){
        // what do we do if name already exist ?
        MetaUI._callback_dict[name] = callback;
    };

    /**
     * Register a preset of UI element in a cell toolbar.
     * Not supported Yet.
     * @method register_preset
     * @param name {String} name to use to refer to the preset. It is advised to use a prefix with the name
     * for easier sorting and avoid collision
     * @param  preset_list {List of String} reverse order of the button in the toolbar. Each String of the list
     *          should correspond to a name of a registerd callback.
     *
     * @private
     * @example
     *
     *      MetaUI.register_callback('foo.c1',function(div,cell){...});
     *      MetaUI.register_callback('foo.c2',function(div,cell){...});
     *      MetaUI.register_callback('foo.c3',function(div,cell){...});
     *      MetaUI.register_callback('foo.c4',function(div,cell){...});
     *      MetaUI.register_callback('foo.c5',function(div,cell){...});
     *
     *      MetaUI.register_preset('foo.foo_preset1',['foo.c1','foo.c2','foo.c5'])
     *      MetaUI.register_preset('foo.foo_preset2',['foo.c4','foo.c5'])
     */
    MetaUI.register_preset = function(name, preset_list){
        MetaUI._presets[name] = preset_list
    }
    /**
     * set an UI preset from `register_preset`
     * @method set_preset
     * @param preset_name {String} string corresponding to the preset name
     *
     * @static
     * @private
     * @example
     *
     *      MetaUI.set_preset('foo.foo_preset1');
     */
    MetaUI.set_preset= function(preset_name){
        var preset = MetaUI._presets[preset_name];

        if(preset != undefined){
            MetaUI._button_list = preset;
            MetaUI.rebuild_all();
        }
    }

    // this is by design not a prototype.
    /**
     * This should be called on the class and not on a instance as it will trigger
     * rebuild of all the instances.
     * @method rebuild_all
     * @static
     *
     */
    MetaUI.rebuild_all = function(){
        for(var i in MetaUI._instances){
            MetaUI._instances[i].rebuild();
        }
    }

    /**
     * Rebuild all the button on the toolbar to update it's state.
     * @method rebuild
     */
    MetaUI.prototype.rebuild = function(){
        // strip evrything from the div
        // which is probabli metainner.
        // or this.element.
        this.metainner.empty();
        //this.add_raw_edit_button()


        var cdict = MetaUI._callback_dict;
        var preset = MetaUI._button_list;
        // Yes we iterate on the class varaible, not the instance one.
        for ( var index in MetaUI._button_list){
            var local_div = $('<div/>').addClass('button_container');
            // Note,
            // do this the other way, wrap in try/catch and don't append if any errors.
            this.metainner.append(local_div)
            cdict[preset[index]](local_div,this.cell)
        }

    }

    var raw_edit = function(cell){

        var md = cell.metadata

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
                           alert('invalid json');
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

    MetaUI.register_callback('example.rawedit',add_raw_edit_button);
    var example_preset = []
    example_preset.push('example.rawedit');

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

    MetaUI.register_callback('default.help',add_simple_dialog_button)
    var default_preset = []
    default_preset.push('default.help')
    MetaUI.register_preset('default',default_preset)
    MetaUI.set_preset('default')

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

    MetaUI.register_callback('example.lock',simple_button);
    example_preset.push('example.lock');

    var toggle_test =  function(div, cell) {
        var button_container = $(div)
        var button = $('<div/>').button({label:String(cell.metadata.foo)});
        button.click(function(){
                    var v = cell.metadata.foo;
                    cell.metadata.foo = !v;
                    button.button("option","label",String(!v));
                })
       button_container.append(button);
    }

    MetaUI.register_callback('example.toggle',toggle_test);
    example_preset.push('example.toggle');

    /**
     */
    MetaUI.utils = {};

    /**
     * A utility function to generate bindings between a checkbox and metadata
     * @method utils.checkbox_ui_generator
     * @static
     *
     * @param name {string} Label in front of the checkbox
     * @param setter {function( metadata_dict, newValue )}
     *        A setter method to set the newValue of the metadata dictionnary
     * @param getter {function( metadata )}
     *        A getter methods which return the current value of the metadata.
     *
     * @return callback {function( div, cell )} Callback to be passed to `register_callback`
     *
     * @example
     *
     * An exmple that bind the subkey `slideshow.isSectionStart` to a checkbox with a `New Slide` label
     *
     *     var newSlide = MetaUI.utils.checkbox_ui_generator('New Slide',
     *          // setter
     *          function(metadata,value){
     *              // we check that the slideshow namespace exist and create it if needed
     *              if (metadata.slideshow == undefined){metadata.slideshow = {}}
     *              // set the value
     *              metadata.slideshow.isSectionStart = value
     *              },
     *          //geter
     *          function(metadata){ var ns = metadata.slideshow;
     *              // if the slideshow namespace does not exist return `undefined`
     *              // (will be interpreted as `false` by checkbox) otherwise
     *              // return the value
     *              return (ns == undefined)? undefined: ns.isSectionStart
     *              }
     *      );
     *
     *      MetaUI.register_callback('newSlide', newSlide);
     *
     */
    MetaUI.utils.checkbox_ui_generator = function(name,setter,getter){
         return function(div, cell) {
            var button_container = $(div)

            var chkb = $('<input/>').attr('type','checkbox');
            var lbl = $('<label/>').append($('<span/>').text(name).css('font-size','77%'));
            lbl.append(chkb);
            chkb.attr("checked",getter(cell.metadata));

            chkb.click(function(){
                        var v = getter(cell.metadata);
                        setter(cell.metadata,!v);
                        chkb.attr("checked",!v);
                    })
           button_container.append($('<div/>').append(lbl));

        }
    }

    /**
     * A utility function to generate bindings between a dropdown list and metadata
     * @method utils.select_ui_generator
     * @static
     *
     * @param list_list {list of sublist} List of sublist of metadata value and name in the dropdown list.
     *        subslit shoud contain 2 element each, first a string that woul be displayed in the dropdown list,
     *        and second the corresponding value for the metadata to be passed to setter/return by getter.
     * @param setter {function( metadata_dict, newValue )}
     *        A setter method to set the newValue of the metadata dictionnary
     * @param getter {function( metadata )}
     *        A getter methods which return the current value of the metadata.
     * @param [label=""] {String} optionnal label for the dropdown menu
     *
     * @return callback {function( div, cell )} Callback to be passed to `register_callback`
     *
     * @example
     *
     *      var select_type = MetaUI.utils.select_ui_generator([
     *              ["-"            ,undefined      ],
     *              ["Header Slide" ,"header_slide" ],
     *              ["Slide"        ,"slide"        ],
     *              ["Fragment"     ,"fragment"     ],
     *              ["Skip"         ,"skip"         ],
     *              ],
     *              // setter
     *              function(metadata,value){
     *                  // we check that the slideshow namespace exist and create it if needed
     *                  if (metadata.slideshow == undefined){metadata.slideshow = {}}
     *                  // set the value
     *                  metadata.slideshow.slide_type = value
     *                  },
     *              //geter
     *              function(metadata){ var ns = metadata.slideshow;
     *                  // if the slideshow namespace does not exist return `undefined`
     *                  // (will be interpreted as `false` by checkbox) otherwise
     *                  // return the value
     *                  return (ns == undefined)? undefined: ns.slide_type
     *                  }
     *      MetaUI.register_callback('slideshow.select',select_type);
     *
     */
    MetaUI.utils.select_ui_generator = function(list_list,setter, getter, label){
        label= label? label: "";
        return function(div, cell) {
            var button_container = $(div)
            var lbl = $("<label/>").append($('<span/>').text(label).css('font-size','77%'));
            var select = $('<select/>');
            for(var itemn in list_list){
                var opt = $('<option/>');
                        opt.attr('value',list_list[itemn][1])
                        opt.text(list_list[itemn][0])
                select.append(opt);
            }
            select.val(getter(cell.metadata));

            select.change(function(){
                        setter(cell.metadata,select.val());
                    });
            button_container.append($('<div/>').append(lbl).append(select));

        }
    };


    IPython.MetaUI = MetaUI;

    return IPython;
}(IPython));
