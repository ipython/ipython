//----------------------------------------------------------------------------
//  Copyright (C) 2008 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ToolBar
//============================================================================
/**
 * @module IPython
 * @namespace IPython
 * @submodule ToolBar
 */

var IPython = (function (IPython) {
    "use strict";

    /**
     * A generic toolbar on which one can add button
     * @class ToolBar
     * @constructor
     * @param {Dom object} selector
     */
    var ToolBar = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
    };

    /**
     *  add a group of button into the current toolbar.
     *
     *
     *  @example
     *
     *      IPython.toolbar.add_buttons_group([
     *          {
     *            label:'my button',
     *            icon:'icon-hdd',
     *            callback:function(){alert('hoho')},
     *            id : 'my_button_id',    // this is optional
     *          },
     *          {
     *            label:'my second button',
     *            icon:'icon-play',
     *            callback:function(){alert('be carefull I cut')}
     *          }
     *        ],
     *        "my_button_group_id"
     *      )
     *
     *  @method add_buttons_group
     *  @param list {List}
     *      List of button of the group, with the following paramter for each :
     *      @param list.label {string} text to show on button hover
     *      @param list.icon {string} icon to choose from [Font Awesome](http://fortawesome.github.io/Font-Awesome)
     *      @param list.callback {function} function to be called on button click
     *      @param [list.id] {String} id to give to the button
     *  @param [group_id] {String} optionnal id to give to the group
     *
     */
    ToolBar.prototype.add_buttons_group = function (list, group_id) {
        var btn_group = $('<div/>').addClass("btn-group");
        if( group_id != undefined ) {
            btn_group.attr('id',group_id);
        }
        for(var el in list) {
            var button  = $('<button/>')
                .addClass('btn')
                .attr("title", list[el].label)
                .append(
                    $("<i/>").addClass(list[el].icon)
                );
            var id = list[el].id;
            if( id != undefined )
                button.attr('id',id);
            var fun = list[el].callback;
            button.click(fun);
            btn_group.append(button);
        }
        $(this.selector).append(btn_group);
    };

    ToolBar.prototype.style = function () {
        this.element.addClass('border-box-sizing')
            .addClass('toolbar');
    };

    /**
     * Show and hide toolbar
     * @method toggle
     */
    ToolBar.prototype.toggle = function () {
        this.element.toggle();
        if (IPython.layout_manager != undefined) {
            IPython.layout_manager.do_resize();
        }
    };


    IPython.ToolBar = ToolBar;

    return IPython;

}(IPython));
