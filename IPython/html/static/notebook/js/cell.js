//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Cell
//============================================================================
/**
 * An extendable module that provide base functionnality to create cell for notebook.
 * @module IPython
 * @namespace IPython
 * @submodule Cell
 */

var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;
    var keycodes = IPython.keyboard.keycodes;

    /**
     * The Base `Cell` class from which to inherit
     * @class Cell
     **/

    /*
     * @constructor
     *
     * @param {object|undefined} [options]
     *     @param [options.cm_config] {object} config to pass to CodeMirror, will extend default parameters
     */
    var Cell = function (options) {

        options = this.mergeopt(Cell, options);
        // superclass default overwrite our default
        
        this.placeholder = options.placeholder || '';
        this.read_only = options.cm_config.readOnly;
        this.selected = false;
        this.rendered = false;
        this.mode = 'command';
        this.metadata = {};
        // load this from metadata later ?
        this.user_highlight = 'auto';
        this.cm_config = options.cm_config;
        this.cell_id = utils.uuid();
        this._options = options;

        // For JS VM engines optimization, attributes should be all set (even
        // to null) in the constructor, and if possible, if different subclass
        // have new attributes with same name, they should be created in the
        // same order. Easiest is to create and set to null in parent class.

        this.element = null;
        this.cell_type = this.cell_type || null;
        this.code_mirror = null;

        this.create_element();
        if (this.element !== null) {
            this.element.data("cell", this);
            this.bind_events();
            this.init_classes();
        }
    };

    Cell.options_default = {
        cm_config : {
            indentUnit : 4,
            readOnly: false,
            theme: "default"
        }
    };
    
    // FIXME: Workaround CM Bug #332 (Safari segfault on drag)
    // by disabling drag/drop altogether on Safari
    // https://github.com/marijnh/CodeMirror/issues/332    
    if (utils.browser[0] == "Safari") {
        Cell.options_default.cm_config.dragDrop = false;
    }

    Cell.prototype.mergeopt = function(_class, options, overwrite){
        options = options || {};
        overwrite = overwrite || {};
        return $.extend(true, {}, _class.options_default, options, overwrite);
    };

    /**
     * Empty. Subclasses must implement create_element.
     * This should contain all the code to create the DOM element in notebook
     * and will be called by Base Class constructor.
     * @method create_element
     */
    Cell.prototype.create_element = function () {
    };

    Cell.prototype.init_classes = function () {
        // Call after this.element exists to initialize the css classes
        // related to selected, rendered and mode.
        if (this.selected) {
            this.element.addClass('selected');
        } else {
            this.element.addClass('unselected');
        }
        if (this.rendered) {
            this.element.addClass('rendered');
        } else {
            this.element.addClass('unrendered');
        }
        if (this.mode === 'edit') {
            this.element.addClass('edit_mode');
        } else {
            this.element.addClass('command_mode');
        }
    };

    /**
     * Subclasses can implement override bind_events.
     * Be carefull to call the parent method when overwriting as it fires event.
     * this will be triggerd after create_element in constructor.
     * @method bind_events
     */
    Cell.prototype.bind_events = function () {
        var that = this;
        // We trigger events so that Cell doesn't have to depend on Notebook.
        that.element.click(function (event) {
            if (!that.selected) {
                $([IPython.events]).trigger('select.Cell', {'cell':that});
            }
        });
        that.element.focusin(function (event) {
            if (!that.selected) {
                $([IPython.events]).trigger('select.Cell', {'cell':that});
            }
        });
        if (this.code_mirror) {
            this.code_mirror.on("change", function(cm, change) {
                $([IPython.events]).trigger("set_dirty.Notebook", {value: true});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('focus', function(cm, change) {
                $([IPython.events]).trigger('edit_mode.Cell', {cell: that});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('blur', function(cm, change) {
                $([IPython.events]).trigger('command_mode.Cell', {cell: that});
            });
        }
    };
    
    /**
     * This method gets called in CodeMirror's onKeyDown/onKeyPress
     * handlers and is used to provide custom key handling.
     *
     * To have custom handling, subclasses should override this method, but still call it
     * in order to process the Edit mode keyboard shortcuts.
     *
     * @method handle_codemirror_keyevent
     * @param {CodeMirror} editor - The codemirror instance bound to the cell
     * @param {event} event - key press event which either should or should not be handled by CodeMirror
     * @return {Boolean} `true` if CodeMirror should ignore the event, `false` Otherwise
     */
    Cell.prototype.handle_codemirror_keyevent = function (editor, event) {
        var that = this;
        var shortcuts = IPython.keyboard_manager.edit_shortcuts;

        // if this is an edit_shortcuts shortcut, the global keyboard/shortcut
        // manager will handle it
        if (shortcuts.handles(event)) { return true; }
        
        return false;
    };


    /**
     * Triger typsetting of math by mathjax on current cell element
     * @method typeset
     */
    Cell.prototype.typeset = function () {
        if (window.MathJax) {
            var cell_math = this.element.get(0);
            MathJax.Hub.Queue(["Typeset", MathJax.Hub, cell_math]);
        }
    };

    /**
     * handle cell level logic when a cell is selected
     * @method select
     * @return is the action being taken
     */
    Cell.prototype.select = function () {
        if (!this.selected) {
            this.element.addClass('selected');
            this.element.removeClass('unselected');
            this.selected = true;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is unselected
     * @method unselect
     * @return is the action being taken
     */
    Cell.prototype.unselect = function () {
        if (this.selected) {
            this.element.addClass('unselected');
            this.element.removeClass('selected');
            this.selected = false;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is rendered
     * @method render
     * @return is the action being taken
     */
    Cell.prototype.render = function () {
        if (!this.rendered) {
            this.element.addClass('rendered');
            this.element.removeClass('unrendered');
            this.rendered = true;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is unrendered
     * @method unrender
     * @return is the action being taken
     */
    Cell.prototype.unrender = function () {
        if (this.rendered) {
            this.element.addClass('unrendered');
            this.element.removeClass('rendered');
            this.rendered = false;
            return true;
        } else {
            return false;
        }
    };

    /**
     * Delegates keyboard shortcut handling to either IPython keyboard
     * manager when in command mode, or CodeMirror when in edit mode
     *
     * @method handle_keyevent
     * @param {CodeMirror} editor - The codemirror instance bound to the cell
     * @param {event} - key event to be handled
     * @return {Boolean} `true` if CodeMirror should ignore the event, `false` Otherwise
     */
    Cell.prototype.handle_keyevent = function (editor, event) {

        // console.log('CM', this.mode, event.which, event.type)

        if (this.mode === 'command') {
            return true;
        } else if (this.mode === 'edit') {
            return this.handle_codemirror_keyevent(editor, event);
        }
    };

    /**
     * @method at_top
     * @return {Boolean}
     */
    Cell.prototype.at_top = function () {
        var cm = this.code_mirror;
        var cursor = cm.getCursor();
        if (cursor.line === 0 && cursor.ch === 0) {
            return true;
        }
        return false;
    };

    /**
     * @method at_bottom
     * @return {Boolean}
     * */
    Cell.prototype.at_bottom = function () {
        var cm = this.code_mirror;
        var cursor = cm.getCursor();
        if (cursor.line === (cm.lineCount()-1) && cursor.ch === cm.getLine(cursor.line).length) {
            return true;
        }
        return false;
    };

    /**
     * enter the command mode for the cell
     * @method command_mode
     * @return is the action being taken
     */
    Cell.prototype.command_mode = function () {
        if (this.mode !== 'command') {
            this.element.addClass('command_mode');
            this.element.removeClass('edit_mode');
            this.mode = 'command';
            return true;
        } else {
            return false;
        }
    };

    /**
     * enter the edit mode for the cell
     * @method command_mode
     * @return is the action being taken
     */
    Cell.prototype.edit_mode = function () {
        if (this.mode !== 'edit') {
            this.element.addClass('edit_mode');
            this.element.removeClass('command_mode');
            this.mode = 'edit';
            return true;
        } else {
            return false;
        }
    };
    
    /**
     * Focus the cell in the DOM sense
     * @method focus_cell
     */
    Cell.prototype.focus_cell = function () {
        this.element.focus();
    };

    /**
     * Focus the editor area so a user can type
     *
     * NOTE: If codemirror is focused via a mouse click event, you don't want to
     * call this because it will cause a page jump.
     * @method focus_editor
     */
    Cell.prototype.focus_editor = function () {
        this.refresh();
        this.code_mirror.focus();
    };

    /**
     * Refresh codemirror instance
     * @method refresh
     */
    Cell.prototype.refresh = function () {
        this.code_mirror.refresh();
    };

    /**
     * should be overritten by subclass
     * @method get_text
     */
    Cell.prototype.get_text = function () {
    };

    /**
     * should be overritten by subclass
     * @method set_text
     * @param {string} text
     */
    Cell.prototype.set_text = function (text) {
    };

    /**
     * should be overritten by subclass
     * serialise cell to json.
     * @method toJSON
     **/
    Cell.prototype.toJSON = function () {
        var data = {};
        data.metadata = this.metadata;
        data.cell_type = this.cell_type;
        return data;
    };


    /**
     * should be overritten by subclass
     * @method fromJSON
     **/
    Cell.prototype.fromJSON = function (data) {
        if (data.metadata !== undefined) {
            this.metadata = data.metadata;
        }
        this.celltoolbar.rebuild();
    };


    /**
     * can the cell be split into two cells
     * @method is_splittable
     **/
    Cell.prototype.is_splittable = function () {
        return true;
    };


    /**
     * can the cell be merged with other cells
     * @method is_mergeable
     **/
    Cell.prototype.is_mergeable = function () {
        return true;
    };


    /**
     * @return {String} - the text before the cursor
     * @method get_pre_cursor
     **/
    Cell.prototype.get_pre_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var text = this.code_mirror.getRange({line:0, ch:0}, cursor);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    };


    /**
     * @return {String} - the text after the cursor
     * @method get_post_cursor
     **/
    Cell.prototype.get_post_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var last_line_num = this.code_mirror.lineCount()-1;
        var last_line_len = this.code_mirror.getLine(last_line_num).length;
        var end = {line:last_line_num, ch:last_line_len};
        var text = this.code_mirror.getRange(cursor, end);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    };

    /**
     * Show/Hide CodeMirror LineNumber
     * @method show_line_numbers
     *
     * @param value {Bool}  show (true), or hide (false) the line number in CodeMirror
     **/
    Cell.prototype.show_line_numbers = function (value) {
        this.code_mirror.setOption('lineNumbers', value);
        this.code_mirror.refresh();
    };

    /**
     * Toggle  CodeMirror LineNumber
     * @method toggle_line_numbers
     **/
    Cell.prototype.toggle_line_numbers = function () {
        var val = this.code_mirror.getOption('lineNumbers');
        this.show_line_numbers(!val);
    };

    /**
     * Force codemirror highlight mode
     * @method force_highlight
     * @param {object} - CodeMirror mode
     **/
    Cell.prototype.force_highlight = function(mode) {
        this.user_highlight = mode;
        this.auto_highlight();
    };

    /**
     * Try to autodetect cell highlight mode, or use selected mode
     * @methods _auto_highlight
     * @private
     * @param {String|object|undefined} - CodeMirror mode | 'auto'
     **/
    Cell.prototype._auto_highlight = function (modes) {
        //Here we handle manually selected modes
        var mode;
        if( this.user_highlight !== undefined &&  this.user_highlight != 'auto' )
        {
            mode = this.user_highlight;
            CodeMirror.autoLoadMode(this.code_mirror, mode);
            this.code_mirror.setOption('mode', mode);
            return;
        }
        var current_mode = this.code_mirror.getOption('mode', mode);
        var first_line = this.code_mirror.getLine(0);
        // loop on every pairs
        for(mode in modes) {
            var regs = modes[mode].reg;
            // only one key every time but regexp can't be keys...
            for(var i=0; i<regs.length; i++) {
                // here we handle non magic_modes
                if(first_line.match(regs[i]) !== null) {
                    if(current_mode == mode){
                        return;
                    }
                    if (mode.search('magic_') !== 0) {
                        this.code_mirror.setOption('mode', mode);
                        CodeMirror.autoLoadMode(this.code_mirror, mode);
                        return;
                    }
                    var open = modes[mode].open || "%%";
                    var close = modes[mode].close || "%%end";
                    var mmode = mode;
                    mode = mmode.substr(6);
                    if(current_mode == mode){
                        return;
                    }
                    CodeMirror.autoLoadMode(this.code_mirror, mode);
                    // create on the fly a mode that swhitch between
                    // plain/text and smth else otherwise `%%` is
                    // source of some highlight issues.
                    // we use patchedGetMode to circumvent a bug in CM
                    CodeMirror.defineMode(mmode , function(config) {
                        return CodeMirror.multiplexingMode(
                        CodeMirror.patchedGetMode(config, 'text/plain'),
                            // always set someting on close
                            {open: open, close: close,
                             mode: CodeMirror.patchedGetMode(config, mode),
                             delimStyle: "delimit"
                            }
                        );
                    });
                    this.code_mirror.setOption('mode', mmode);
                    return;
                }
            }
        }
        // fallback on default
        var default_mode;
        try {
            default_mode = this._options.cm_config.mode;
        } catch(e) {
            default_mode = 'text/plain';
        }
        if( current_mode === default_mode){
            return;
        }
        this.code_mirror.setOption('mode', default_mode);
    };

    IPython.Cell = Cell;

    return IPython;

}(IPython));

