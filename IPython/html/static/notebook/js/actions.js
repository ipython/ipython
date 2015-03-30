// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define(function(require){
    "use strict";
    
    var ActionHandler = function (env) {
        this.env = env || {};
        Object.seal(this);
    };

    /**
     *  A bunch of predefined `Simple Actions` used by IPython.
     *  `Simple Actions` have the following keys:
     *  help (optional): a short string the describe the action.
     *      will be used in various context, like as menu name, tool tips on buttons,
     *      and short description in help menu.
     *  help_index (optional): a string used to sort action in help menu.
     *  icon (optional): a short string that represent the icon that have to be used with this
     *  action. this should mainly correspond to a Font_awesome class.
     *  handler : a function which is called when the action is activated. It will receive at first parameter
     *      a dictionary containing various handle to element of the notebook.
     *
     *  action need to be registered with a **name** that can be use to refer to this action.
     *
     *
     *  if `help` is not provided it will be derived by replacing any dash by space
     *  in the **name** of the action. It is advised to provide a prefix to action name to
     *  avoid conflict the prefix should be all lowercase and end with a dot `.`
     *  in the absence of a prefix the behavior of the action is undefined.
     *
     *  All action provided by IPython are prefixed with `ipython.`.
     *
     *  One can register extra actions or replace an existing action with another one is possible
     *  but is considered undefined behavior.
     *
     **/
    var _actions = {
        'run-select-next': {
            icon: 'fa-play',
            help    : 'run cell, select below',
            help_index : 'ba',
            handler : function (env) {
                env.notebook.execute_cell_and_select_below();
            }
        },
        'execute-in-place':{
            help    : 'run cell',
            help_index : 'bb',
            handler : function (env) {
                env.notebook.execute_cell();
            }
        },
        'execute-and-insert-after':{
            help    : 'run cell, insert below',
            help_index : 'bc',
            handler : function (env) {
                env.notebook.execute_cell_and_insert_below();
            }
        },
        'go-to-command-mode': {
            help    : 'command mode',
            help_index : 'aa',
            handler : function (env) {
                env.notebook.command_mode();
            }
        },
        'split-cell-at-cursor': {
            help    : 'split cell',
            help_index : 'ea',
            handler : function (env) {
                env.notebook.split_cell();
            }
        },
        'enter-edit-mode' : {
            help_index : 'aa',
            handler : function (env) {
                env.notebook.edit_mode();
            }
        },
        'select-previous-cell' : {
            help: 'select cell above',
            help_index : 'da',
            handler : function (env) {
                var index = env.notebook.get_selected_index();
                if (index !== 0 && index !== null) {
                    env.notebook.select_prev();
                    env.notebook.focus_cell();
                }
            }
        },
        'select-next-cell' : {
            help: 'select cell below',
            help_index : 'db',
            handler : function (env) {
                var index = env.notebook.get_selected_index();
                if (index !== (env.notebook.ncells()-1) && index !== null) {
                    env.notebook.select_next();
                    env.notebook.focus_cell();
                }
            }
        },
        'cut-selected-cell' : {
            icon: 'fa-cut',
            help_index : 'ee',
            handler : function (env) {
                var index = env.notebook.get_selected_index();
                env.notebook.cut_cell();
                env.notebook.select(index);
            }
        },
        'copy-selected-cell' : {
            icon: 'fa-copy',
            help_index : 'ef',
            handler : function (env) {
                env.notebook.copy_cell();
            }
        },
        'paste-cell-before' : {
            help: 'paste cell above',
            help_index : 'eg',
            handler : function (env) {
                env.notebook.paste_cell_above();
            }
        },
        'paste-cell-after' : {
            help: 'paste cell below',
            icon: 'fa-paste',
            help_index : 'eh',
            handler : function (env) {
                env.notebook.paste_cell_below();
            }
        },
        'insert-cell-before' : {
            help: 'insert cell above',
            help_index : 'ec',
            handler : function (env) {
                env.notebook.insert_cell_above();
                env.notebook.select_prev();
                env.notebook.focus_cell();
            }
        },
        'insert-cell-after' : {
            help: 'insert cell below',
            icon : 'fa-plus',
            help_index : 'ed',
            handler : function (env) {
                env.notebook.insert_cell_below();
                env.notebook.select_next();
                env.notebook.focus_cell();
            }
        },
        'change-selected-cell-to-code-cell' : {
            help    : 'to code',
            help_index : 'ca',
            handler : function (env) {
                env.notebook.to_code();
            }
        },
        'change-selected-cell-to-markdown-cell' : {
            help    : 'to markdown',
            help_index : 'cb',
            handler : function (env) {
                env.notebook.to_markdown();
            }
        },
        'change-selected-cell-to-raw-cell' : {
            help    : 'to raw',
            help_index : 'cc',
            handler : function (env) {
                env.notebook.to_raw();
            }
        },
        'change-selected-cell-to-heading-1' : {
            help    : 'to heading 1',
            help_index : 'cd',
            handler : function (env) {
                env.notebook.to_heading(undefined, 1);
            }
        },
        'change-selected-cell-to-heading-2' : {
            help    : 'to heading 2',
            help_index : 'ce',
            handler : function (env) {
                env.notebook.to_heading(undefined, 2);
            }
        },
        'change-selected-cell-to-heading-3' : {
            help    : 'to heading 3',
            help_index : 'cf',
            handler : function (env) {
                env.notebook.to_heading(undefined, 3);
            }
        },
        'change-selected-cell-to-heading-4' : {
            help    : 'to heading 4',
            help_index : 'cg',
            handler : function (env) {
                env.notebook.to_heading(undefined, 4);
            }
        },
        'change-selected-cell-to-heading-5' : {
            help    : 'to heading 5',
            help_index : 'ch',
            handler : function (env) {
                env.notebook.to_heading(undefined, 5);
            }
        },
        'change-selected-cell-to-heading-6' : {
            help    : 'to heading 6',
            help_index : 'ci',
            handler : function (env) {
                env.notebook.to_heading(undefined, 6);
            }
        },
        'toggle-output-visibility-selected-cell' : {
            help    : 'toggle output',
            help_index : 'gb',
            handler : function (env) {
                env.notebook.toggle_output();
            }
        },
        'toggle-output-scrolling-selected-cell' : {
            help    : 'toggle output scrolling',
            help_index : 'gc',
            handler : function (env) {
                env.notebook.toggle_output_scroll();
            }
        },
        'move-selected-cell-down' : {
            icon: 'fa-arrow-down',
            help_index : 'eb',
            handler : function (env) {
                env.notebook.move_cell_down();
            }
        },
        'move-selected-cell-up' : {
            icon: 'fa-arrow-up',
            help_index : 'ea',
            handler : function (env) {
                env.notebook.move_cell_up();
            }
        },
        'toggle-line-number-selected-cell' : {
            help    : 'toggle line numbers',
            help_index : 'ga',
            handler : function (env) {
                env.notebook.cell_toggle_line_numbers();
            }
        },
        'show-keyboard-shortcut-help-dialog' : {
            help_index : 'ge',
            handler : function (env) {
                env.quick_help.show_keyboard_shortcuts();
            }
        },
        'delete-cell': {
            help: 'delete selected cell',
            help_index : 'ej',
            handler : function (env) {
                env.notebook.delete_cell();
            }
        },
        'interrupt-kernel':{
            icon: 'fa-stop',
            help_index : 'ha',
            handler : function (env) {
                env.notebook.kernel.interrupt();
            }
        },
        'restart-kernel':{
            icon: 'fa-repeat',
            help_index : 'hb',
            handler : function (env) {
                env.notebook.restart_kernel();
            }
        },
        'undo-last-cell-deletion' : {
            help_index : 'ei',
            handler : function (env) {
                env.notebook.undelete_cell();
            }
        },
        'merge-selected-cell-with-cell-after' : {
            help    : 'merge cell below',
            help_index : 'ek',
            handler : function (env) {
                env.notebook.merge_cell_below();
            }
        },
        'close-pager' : {
            help_index : 'gd',
            handler : function (env) {
                env.pager.collapse();
            }
        }

    };

    /**
     * A bunch of `Advance actions` for IPython.
     * Cf `Simple Action` plus the following properties.
     *
     * handler: first argument of the handler is the event that triggerd the action
     *      (typically keypress). The handler is responsible for any modification of the
     *      event and event propagation.
     *      Is also responsible for returning false if the event have to be further ignored,
     *      true, to tell keyboard manager that it ignored the event.
     *
     *      the second parameter of the handler is the environemnt passed to Simple Actions
     *
     **/
    var custom_ignore = {
        'ignore':{
            handler : function () {
                return true;
            }
        },
        'move-cursor-up-or-previous-cell':{
            handler : function (env, event) {
                var index = env.notebook.get_selected_index();
                var cell = env.notebook.get_cell(index);
                var cm = env.notebook.get_selected_cell().code_mirror;
                var cur = cm.getCursor();
                if (cell && cell.at_top() && index !== 0 && cur.ch === 0) {
                    if(event){
                        event.preventDefault();
                    }
                    env.notebook.command_mode();
                    env.notebook.select_prev();
                    env.notebook.edit_mode();
                    cm = env.notebook.get_selected_cell().code_mirror;
                    cm.setCursor(cm.lastLine(), 0);
                }
                return false;
            }
        },
        'move-cursor-down-or-next-cell':{
            handler : function (env, event) {
                var index = env.notebook.get_selected_index();
                var cell = env.notebook.get_cell(index);
                if (cell.at_bottom() && index !== (env.notebook.ncells()-1)) {
                    if(event){
                        event.preventDefault();
                    }
                    env.notebook.command_mode();
                    env.notebook.select_next();
                    env.notebook.edit_mode();
                    var cm = env.notebook.get_selected_cell().code_mirror;
                    cm.setCursor(0, 0);
                }
                return false;
            }
        },
        'scroll-down': {
            handler: function(env, event) {
                if(event){
                    event.preventDefault();
                }
                return env.notebook.scroll_manager.scroll(1);
            },
        },
        'scroll-up': {
            handler: function(env, event) {
                if(event){
                    event.preventDefault();
                }
                return env.notebook.scroll_manager.scroll(-1);
            },
        },
        'save-notebook':{
            help: "Save and Checkpoint",
            help_index : 'fb',
            icon: 'fa-save',
            handler : function (env, event) {
                env.notebook.save_checkpoint();
                if(event){
                    event.preventDefault();
                }
                return false;
            }
        },
    };

    // private stuff that prepend `.ipython` to actions names
    // and uniformize/fill in missing pieces in of an action.
    var _prepare_handler = function(registry, subkey, source){
        registry['ipython.'+subkey] = {};
        registry['ipython.'+subkey].help = source[subkey].help||subkey.replace(/-/g,' ');
        registry['ipython.'+subkey].help_index = source[subkey].help_index;
        registry['ipython.'+subkey].icon = source[subkey].icon;
        return source[subkey].handler;
    };

    // Will actually generate/register all the IPython actions
    var fun = function(){
        var final_actions = {};
        var k;
        for(k in _actions){
            if(_actions.hasOwnProperty(k)){
                // Js closure are function level not block level need to wrap in a IIFE
                // and append ipython to event name these things do intercept event so are wrapped
                // in a function that return false.
                var handler = _prepare_handler(final_actions, k, _actions);
                (function(key, handler){
                    final_actions['ipython.'+key].handler = function(env, event){
                        handler(env);
                        if(event){
                            event.preventDefault();
                        }
                        return false;
                    };
                })(k, handler);
            }
        }

        for(k in custom_ignore){
            // Js closure are function level not block level need to wrap in a IIFE
            // same as above, but decide for themselves wether or not they intercept events.
            if(custom_ignore.hasOwnProperty(k)){
                var handler = _prepare_handler(final_actions, k, custom_ignore);
                (function(key, handler){
                    final_actions['ipython.'+key].handler = function(env, event){
                        return handler(env, event);
                    };
                })(k, handler);
            }
        }

        return final_actions;
    };
    ActionHandler.prototype._actions = fun();


    /**
     *  extend the environment variable that will be pass to handlers
     **/
    ActionHandler.prototype.extend_env = function(env){
        for(var k in env){
            this.env[k] = env[k];
        }
    };

    ActionHandler.prototype.register = function(action, name, prefix){
        /**
         * Register an `action` with an optional name and prefix. 
         *
         * if name and prefix are not given they will be determined automatically. 
         * if action if just a `function` it will be wrapped in an anonymous action.
         *
         * @return the full name to access this action .
         **/
        action = this.normalise(action);
        if( !name ){
            name = 'autogenerated-'+String(action.handler);
        }
        prefix = prefix || 'auto';
        var full_name = prefix+'.'+name;
        this._actions[full_name] = action;
        return full_name;

    };


    ActionHandler.prototype.normalise = function(data){
        /**
         * given an `action` or `function`, return a normalised `action`
         * by setting all known attributes and removing unknown attributes;
         **/
        if(typeof(data) === 'function'){
            data = {handler:data};
        }
        if(typeof(data.handler) !== 'function'){
            throw('unknown datatype, cannot register');
        }
        var _data = data;
        data = {};
        data.handler = _data.handler;
        data.help = _data.help || '';
        data.icon = _data.icon || '';
        data.help_index = _data.help_index || '';
        return data;
    };

    ActionHandler.prototype.get_name = function(name_or_data){
        /**
         * given an `action` or `name` of a action, return the name attached to this action.
         * if given the name of and corresponding actions does not exist in registry, return `null`.
         **/

        if(typeof(name_or_data) === 'string'){
            if(this.exists(name_or_data)){
                return name_or_data;
            } else {
                return null;
            }
        } else {
            return this.register(name_or_data);
        }
    };

    ActionHandler.prototype.get = function(name){
        return this._actions[name];
    };

    ActionHandler.prototype.call = function(name, event, env){
        return this._actions[name].handler(env|| this.env, event);
    };

    ActionHandler.prototype.exists = function(name){
        return (typeof(this._actions[name]) !== 'undefined');
    };

    return {init:ActionHandler};

});
