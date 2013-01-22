//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CellToolbar
//============================================================================


/**
 * A Module to control the per-cell toolbar.
 * @module IPython
 * @namespace IPython
 * @submodule CellToolbar
 */
var IPython = (function (IPython) {
    "use strict";

    /**
     * @constructor
     * @class CellToolbar
     * @param {The cell to attach the metadata UI to} cell
     */
    var CellToolbar = function (cell) {
        CellToolbar._instances.push(this);
        this.cell = cell;
        this.create_element();
        this.rebuild();
        return this;
    };


    CellToolbar.prototype.create_element = function () {
        this.inner_element = $('<div/>');
        var ctb_element = $('<div/>').addClass('celltoolbar')
            .append(this.inner_element);
        ctb_element.addClass('box-flex1');
        var ctb_area = $('<div/>').addClass('ctb_area hbox');
        var ctb_prompt = $('<div/>').addClass('ctb_prompt prompt');
        ctb_area.append(ctb_prompt).append(ctb_element);
        this.element = $('<div/>').addClass('ctb_hideshow')
            .append(ctb_area);
    };


    // The default css style for the outer celltoolbar div
    // (ctb_hideshow) is display: none. We add the ctb_show
    // class to either 1) the body to show all cell's toolbars
    // or 2) to the individual celltoolbar divs to show just one
    // cell's toolbar.

    CellToolbar.global_hide = function () {
        $('body').removeClass('ctb_show');
    }


    CellToolbar.global_show = function () {
       $('body').addClass('ctb_show');
    }


    CellToolbar.prototype.hide = function () {
        this.element.removeClass('ctb_show');
    }


    CellToolbar.prototype.show = function () {
        this.element.addClass('ctb_show');
    }


    /**
     * Class variable that should contain a dict of all availlable callback
     * we need to think of wether or not we allow nested namespace
     * @property _callback_dict
     * @private
     * @static
     * @type Dict
     */
    CellToolbar._callback_dict = {};


    /**
     * Class variable that should contain the reverse order list of the button
     * to add to the toolbar of each cell
     * @property _ui_controls_list
     * @private
     * @static
     * @type List
     */
    CellToolbar._ui_controls_list = [];


    /**
     * Class variable that should contains the CellToolbar instances for each
     * cell of the notebook
     *
     * @private
     * @property _instances
     * @static
     * @type List
     */
    CellToolbar._instances =[]


    /**
     * keep a list of all the availlabel presets for the toolbar
     * @private
     * @property _presets
     * @static
     * @type Dict
     */
    CellToolbar._presets ={}


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
     *    * the cell it is responsible from
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
     *                      button.button("option", "label", String(!v));
     *                  })
     *
     *          // add the button to the DOM div.
     *          button_container.append(button);
     *      }
     *
     *      // now we register the callback under the name `foo` to give the
     *      // user the ability to use it later
     *      CellToolbar.register_callback('foo', toggle);
     */
    CellToolbar.register_callback = function(name, callback){
        // Overwrite if it already exists.
        CellToolbar._callback_dict[name] = callback;
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
     *      CellToolbar.register_callback('foo.c1', function(div, cell){...});
     *      CellToolbar.register_callback('foo.c2', function(div, cell){...});
     *      CellToolbar.register_callback('foo.c3', function(div, cell){...});
     *      CellToolbar.register_callback('foo.c4', function(div, cell){...});
     *      CellToolbar.register_callback('foo.c5', function(div, cell){...});
     *
     *      CellToolbar.register_preset('foo.foo_preset1', ['foo.c1', 'foo.c2', 'foo.c5'])
     *      CellToolbar.register_preset('foo.foo_preset2', ['foo.c4', 'foo.c5'])
     */
    CellToolbar.register_preset = function(name, preset_list) {
        CellToolbar._presets[name] = preset_list
        $([IPython.events]).trigger('preset_added.CellToolbar', {name: name});
    };


    /**
     * List the names of the presets that are currently registered.
     *
     * @method list_presets
     * @static
     */
    CellToolbar.list_presets = function() {
        var keys = [];
        for (var k in CellToolbar._presets) {
            keys.push(k);
        }
        return keys;
    };


    /**
     * Activate an UI preset from `register_preset`
     *
     * This does not update the selection UI.
     *
     * @method activate_preset
     * @param preset_name {String} string corresponding to the preset name
     *
     * @static
     * @private
     * @example
     *
     *      CellToolbar.activate_preset('foo.foo_preset1');
     */
    CellToolbar.activate_preset= function(preset_name){
        var preset = CellToolbar._presets[preset_name];

        if(preset != undefined){
            CellToolbar._ui_controls_list = preset;
            CellToolbar.rebuild_all();
        }
    }


    /**
     * This should be called on the class and not on a instance as it will trigger
     * rebuild of all the instances.
     * @method rebuild_all
     * @static
     *
     */
    CellToolbar.rebuild_all = function(){
        for(var i in CellToolbar._instances){
            CellToolbar._instances[i].rebuild();
        }
    }

    /**
     * Rebuild all the button on the toolbar to update it's state.
     * @method rebuild
     */
    CellToolbar.prototype.rebuild = function(){
        // strip evrything from the div
        // which is probabli metainner.
        // or this.element.
        this.inner_element.empty();

        var cdict = CellToolbar._callback_dict;
        var preset = CellToolbar._ui_controls_list;
        // Yes we iterate on the class varaible, not the instance one.
        for ( var index in CellToolbar._ui_controls_list){
            var local_div = $('<div/>').addClass('button_container');
            // Note,
            // do this the other way, wrap in try/catch and don't append if any errors.
            this.inner_element.append(local_div)
            cdict[preset[index]](local_div, this.cell)
        }
    }


    /**
     */
    CellToolbar.utils = {};


    /**
     * A utility function to generate bindings between a checkbox and cell/metadata
     * @method utils.checkbox_ui_generator
     * @static
     *
     * @param name {string} Label in front of the checkbox
     * @param setter {function( cell, newValue )}
     *        A setter method to set the newValue
     * @param getter {function( cell )}
     *        A getter methods which return the current value.
     *
     * @return callback {function( div, cell )} Callback to be passed to `register_callback`
     *
     * @example
     *
     * An exmple that bind the subkey `slideshow.isSectionStart` to a checkbox with a `New Slide` label
     *
     *     var newSlide = CellToolbar.utils.checkbox_ui_generator('New Slide',
     *          // setter
     *          function(cell, value){
     *              // we check that the slideshow namespace exist and create it if needed
     *              if (cell.metadata.slideshow == undefined){cell.metadata.slideshow = {}}
     *              // set the value
     *              cell.metadata.slideshow.isSectionStart = value
     *              },
     *          //geter
     *          function(cell){ var ns = cell.metadata.slideshow;
     *              // if the slideshow namespace does not exist return `undefined`
     *              // (will be interpreted as `false` by checkbox) otherwise
     *              // return the value
     *              return (ns == undefined)? undefined: ns.isSectionStart
     *              }
     *      );
     *
     *      CellToolbar.register_callback('newSlide', newSlide);
     *
     */
    CellToolbar.utils.checkbox_ui_generator = function(name, setter, getter){
         return function(div, cell) {
            var button_container = $(div)

            var chkb = $('<input/>').attr('type', 'checkbox');
            var lbl = $('<label/>').append($('<span/>').text(name));
            lbl.append(chkb);
            chkb.attr("checked", getter(cell));

            chkb.click(function(){
                        var v = getter(cell);
                        setter(cell, !v);
                        chkb.attr("checked", !v);
                    })
           button_container.append($('<div/>').append(lbl));

        }
    }


    /**
     * A utility function to generate bindings between a dropdown list cell
     * @method utils.select_ui_generator
     * @static
     *
     * @param list_list {list of sublist} List of sublist of metadata value and name in the dropdown list.
     *        subslit shoud contain 2 element each, first a string that woul be displayed in the dropdown list,
     *        and second the corresponding value to  be passed to setter/return by getter.
     * @param setter {function( cell, newValue )}
     *        A setter method to set the newValue
     * @param getter {function( cell )}
     *        A getter methods which return the current value of the metadata.
     * @param [label=""] {String} optionnal label for the dropdown menu
     *
     * @return callback {function( div, cell )} Callback to be passed to `register_callback`
     *
     * @example
     *
     *      var select_type = CellToolbar.utils.select_ui_generator([
     *              ["<None>"            , undefined      ],
     *              ["Header Slide" , "header_slide" ],
     *              ["Slide"        , "slide"        ],
     *              ["Fragment"     , "fragment"     ],
     *              ["Skip"         , "skip"         ],
     *              ],
     *              // setter
     *              function(cell, value){
     *                  // we check that the slideshow namespace exist and create it if needed
     *                  if (cell.metadata.slideshow == undefined){cell.metadata.slideshow = {}}
     *                  // set the value
     *                  cell.metadata.slideshow.slide_type = value
     *                  },
     *              //geter
     *              function(cell){ var ns = cell.metadata.slideshow;
     *                  // if the slideshow namespace does not exist return `undefined`
     *                  // (will be interpreted as `false` by checkbox) otherwise
     *                  // return the value
     *                  return (ns == undefined)? undefined: ns.slide_type
     *                  }
     *      CellToolbar.register_callback('slideshow.select', select_type);
     *
     */
    CellToolbar.utils.select_ui_generator = function(list_list, setter, getter, label){
        label= label? label: "";
        return function(div, cell) {
            var button_container = $(div)
            var lbl = $("<label/>").append($('<span/>').text(label));
            var select = $('<select/>').addClass('ui-widget ui-widget-content');
            for(var itemn in list_list){
                var opt = $('<option/>');
                        opt.attr('value', list_list[itemn][1])
                        opt.text(list_list[itemn][0])
                select.append(opt);
            }
            select.val(getter(cell));
            select.change(function(){
                        setter(cell, select.val());
                    });
            button_container.append($('<div/>').append(lbl).append(select));

        }
    };


    IPython.CellToolbar = CellToolbar;

    return IPython;
}(IPython));
