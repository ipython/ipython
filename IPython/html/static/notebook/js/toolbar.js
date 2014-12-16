// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery'
], function(IPython, $) {
    "use strict";

    /**
     * A generic toolbar on which one can add button
     * @class ToolBar
     * @constructor
     * @param {Dom_object} selector
     */
    var ToolBar = function (selector, options) {
        this.selector = selector;
        this.actions = (options||{}).actions;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
    };

    ToolBar.prototype._pseudo_actions={};


    ToolBar.prototype.construct = function (config) {
        for(var k=0; k<config.length; k++) {
            this.add_buttons_group(config[k][0],config[k][1]);
        }
    };

    /**
     *  Add a group of button into the current toolbar.
     *
     *  Use a [dict of [list of action name]] to trigger
     *  on click to the button
     *
     *  @example
     *
     *      ... todo, maybe use a list of  list to keep ordering.
     *
     *      [
     *          [
     *            [
     *              action_name_1,
     *              action_name_2,
     *              action_name_3,
     *            ],
     *            optional_group_name
     *          ],
     *          ...
     *      ]
     *
     *  For backward compatibility this also support the
     *  old methods of adding a button directly bound to callbacks:
     *  @example
     *      # deprecate, do not use
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
     *
     *  for private usage, the key can also be strings starting with '<' and ending with '>' to inject custom element that cannot
     *  be bound to an action.
     *
     */
    // TODO JUPYTER:
    // get rid of legacy code that handle things that are not actions.
    ToolBar.prototype.add_buttons_group = function (list, group_id) {
        // handle custom call of pseudoaction binding.
        if(typeof(list) === 'string' && list.slice(0,1) === '<' && list.slice(-1) === '>'){
            var _pseudo_action;
            try{
                _pseudo_action = list.slice(1,-1);
                this.element.append(this._pseudo_actions[_pseudo_action].call(this));
            } catch (e) {
                console.warn('ouch, calling ', _pseudo_action, 'does not seem to work...:', e);
            }
            return ;
        }
        var that = this;
        var btn_group = $('<div/>').addClass("btn-group");
        if( group_id !== undefined ) {
            btn_group.attr('id',group_id);
        }
        for(var i=0; i < list.length; i++) {

            // IIFE because javascript don't have loop scope so
            // action_name would otherwise be the same on all iteration
            // of the loop
            (function(i,list){
                var el = list[i];
                var action_name;
                var action;
                if(typeof(el) === 'string'){
                    action = that.actions.get(el);
                    action_name = el;

                }
                var button  = $('<button/>')
                    .addClass('btn btn-default')
                    .attr("title", el.label||action.help)
                    .append(
                        $("<i/>").addClass(el.icon||action.icon).addClass('fa')
                    );
                var id = el.id;
                if( id !== undefined ){
                    button.attr('id',id);
                }
                button.attr('data-jupyter-action', action_name);
                var fun = el.callback|| function(){
                    that.actions.call(action_name);
                };
                button.click(fun);
                btn_group.append(button);
            })(i,list);
            // END IIFE
        }
        $(this.selector).append(btn_group);
    };

    ToolBar.prototype.style = function () {
        this.element.addClass('toolbar');
    };

    /**
     * Show and hide toolbar
     * @method toggle
     */
    ToolBar.prototype.toggle = function () {
        this.element.toggle();
    };

    // Backwards compatibility.
    IPython.ToolBar = ToolBar;

    return {'ToolBar': ToolBar};
});
