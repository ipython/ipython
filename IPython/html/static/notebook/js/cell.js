// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

/**
 *
 *
 * @module cell
 * @namespace cell
 * @class Cell
 */


define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'codemirror/lib/codemirror',
    'codemirror/addon/edit/matchbrackets',
    'codemirror/addon/edit/closebrackets',
    'codemirror/addon/comment/comment'
], function(IPython, $, utils, CodeMirror, cm_match, cm_closeb, cm_comment) {
    // TODO: remove IPython dependency here 
    "use strict";
    
    var overlayHack = CodeMirror.scrollbarModel.native.prototype.overlayHack;
    
    CodeMirror.scrollbarModel.native.prototype.overlayHack = function () {
        overlayHack.apply(this, arguments);
        // Reverse `min-height: 18px` scrollbar hack on OS X
        // which causes a dead area, making it impossible to click on the last line
        // when there is horizontal scrolling to do and the "show scrollbar only when scrolling" behavior
        // is enabled.
        // This, in turn, has the undesirable behavior of never showing the horizontal scrollbar,
        // even when it should, which is less problematic, at least.
        if (/Mac/.test(navigator.platform)) {
            this.horiz.style.minHeight = "";
        }
    };
    
    var Cell = function (options) {
        /* Constructor
         *
         * The Base `Cell` class from which to inherit.
         * @constructor
         * @param:
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          events: $(Events) instance
         *          config: dictionary
         *          keyboard_manager: KeyboardManager instance
         */
        options = options || {};
        this.keyboard_manager = options.keyboard_manager;
        this.events = options.events;
        var config = utils.mergeopt(Cell, options.config);
        // superclass default overwrite our default
        
        this.placeholder = config.placeholder || '';
        this.selected = false;
        this.rendered = false;
        this.mode = 'command';

        // Metadata property
        var that = this;
        this._metadata = {};
        Object.defineProperty(this, 'metadata', {
            get: function() { return that._metadata; },
            set: function(value) {
                that._metadata = value;
                if (that.celltoolbar) {
                    that.celltoolbar.rebuild();
                }
            }
        });

        // load this from metadata later ?
        this.user_highlight = 'auto';

        var _local_cm_config = {};
        if(this.class_config){
            _local_cm_config = this.class_config.get_sync('cm_config');
        }
        this.cm_config = utils.mergeopt({}, config.cm_config, _local_cm_config);
        this.cell_id = utils.uuid();
        this._options = config;

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
            theme: "default",
            extraKeys: {
                "Cmd-Right":"goLineRight",
                "End":"goLineRight",
                "Cmd-Left":"goLineLeft"
            }
        }
    };
    
    // FIXME: Workaround CM Bug #332 (Safari segfault on drag)
    // by disabling drag/drop altogether on Safari
    // https://github.com/codemirror/CodeMirror/issues/332    
    if (utils.browser[0] == "Safari") {
        Cell.options_default.cm_config.dragDrop = false;
    }

    /**
     * Empty. Subclasses must implement create_element.
     * This should contain all the code to create the DOM element in notebook
     * and will be called by Base Class constructor.
     * @method create_element
     */
    Cell.prototype.create_element = function () {
    };

    Cell.prototype.init_classes = function () {
        /**
         * Call after this.element exists to initialize the css classes
         * related to selected, rendered and mode.
         */
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
                that.events.trigger('select.Cell', {'cell':that});
            }
        });
        that.element.focusin(function (event) {
            if (!that.selected) {
                that.events.trigger('select.Cell', {'cell':that});
            }
        });
        if (this.code_mirror) {
            this.code_mirror.on("change", function(cm, change) {
                that.events.trigger("set_dirty.Notebook", {value: true});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('focus', function(cm, change) {
                that.events.trigger('edit_mode.Cell', {cell: that});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('blur', function(cm, change) {
                that.events.trigger('command_mode.Cell', {cell: that});
            });
        }

        this.element.dblclick(function () {
            if (that.selected === false) {
                this.events.trigger('select.Cell', {'cell':that});
            }
            var cont = that.unrender();
            if (cont) {
                that.focus_editor();
            }
        });
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
        var shortcuts = this.keyboard_manager.edit_shortcuts;

        var cur = editor.getCursor();
        if((cur.line !== 0 || cur.ch !==0) && event.keyCode === 38){
            event._ipkmIgnore = true;
        }
        var nLastLine = editor.lastLine();
        if ((event.keyCode === 40) &&
             ((cur.line !== nLastLine) ||
               (cur.ch !== editor.getLineHandle(nLastLine).text.length))
           ) {
            event._ipkmIgnore = true;
        }
        // if this is an edit_shortcuts shortcut, the global keyboard/shortcut
        // manager will handle it
        if (shortcuts.handles(event)) {
            return true;
        }
        
        return false;
    };


    /**
     * Triger typsetting of math by mathjax on current cell element
     * @method typeset
     */
    Cell.prototype.typeset = function () {
        utils.typeset(this.element);
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
     * should be overritten by subclass
     * @method execute
     */
    Cell.prototype.execute = function () {
        return;
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
            this.mode = 'edit';
            return true;
        } else {
            return false;
        }
    };

    Cell.prototype.ensure_focused = function() {
        if(this.element !== document.activeElement && !this.code_mirror.hasFocus()){
            this.focus_cell();
        }
    }
    
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
        if (this.code_mirror) {
            this.code_mirror.refresh();
        }
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
        // deepcopy the metadata so copied cells don't share the same object
        data.metadata = JSON.parse(JSON.stringify(this.metadata));
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
    };


    /**
     * can the cell be split into two cells (false if not deletable)
     * @method is_splittable
     **/
    Cell.prototype.is_splittable = function () {
        return this.is_deletable();
    };


    /**
     * can the cell be merged with other cells (false if not deletable)
     * @method is_mergeable
     **/
    Cell.prototype.is_mergeable = function () {
        return this.is_deletable();
    };

    /**
     * is the cell deletable? only false (undeletable) if
     * metadata.deletable is explicitly false -- everything else
     * counts as true
     *
     * @method is_deletable
     **/
    Cell.prototype.is_deletable = function () {
        if (this.metadata.deletable === false) {
            return false;
        }
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
     * Trigger autodetection of highlight scheme for current cell
     * @method auto_highlight
     */
    Cell.prototype.auto_highlight = function () {
        this._auto_highlight(this.class_config.get_sync('highlight_modes'));
    };
    
    /**
     * Try to autodetect cell highlight mode, or use selected mode
     * @methods _auto_highlight
     * @private
     * @param {String|object|undefined} - CodeMirror mode | 'auto'
     **/
    Cell.prototype._auto_highlight = function (modes) {
        /**
         *Here we handle manually selected modes
         */
        var that = this;
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
                // here we handle non magic_modes.
                // TODO :
                // On 3.0 and below, these things were regex.
                // But now should be string for json-able config. 
                // We should get rid of assuming they might be already 
                // in a later version of IPython. 
                var re = regs[i];
                if(typeof(re) === 'string'){
                    re = new RegExp(re) 
                }
                if(first_line.match(re) !== null) {
                    if(current_mode == mode){
                        return;
                    }
                    if (mode.search('magic_') !== 0) {
                        utils.requireCodeMirrorMode(mode, function (spec) {
                            that.code_mirror.setOption('mode', spec);
                        });
                        return;
                    }
                    var open = modes[mode].open || "%%";
                    var close = modes[mode].close || "%%end";
                    var magic_mode = mode;
                    mode = magic_mode.substr(6);
                    if(current_mode == magic_mode){
                        return;
                    }
                    utils.requireCodeMirrorMode(mode, function (spec) {
                        // create on the fly a mode that switch between
                        // plain/text and something else, otherwise `%%` is
                        // source of some highlight issues.
                        CodeMirror.defineMode(magic_mode, function(config) {
                            return CodeMirror.multiplexingMode(
                                CodeMirror.getMode(config, 'text/plain'),
                                // always set something on close
                                {open: open, close: close,
                                 mode: CodeMirror.getMode(config, spec),
                                 delimStyle: "delimit"
                                }
                            );
                        });
                        that.code_mirror.setOption('mode', magic_mode);
                    });
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

    var UnrecognizedCell = function (options) {
        /** Constructor for unrecognized cells */
        Cell.apply(this, arguments);
        this.cell_type = 'unrecognized';
        this.celltoolbar = null;
        this.data = {};
        
        Object.seal(this);
    };

    UnrecognizedCell.prototype = Object.create(Cell.prototype);
    
    
    // cannot merge or split unrecognized cells
    UnrecognizedCell.prototype.is_mergeable = function () {
        return false;
    };
    
    UnrecognizedCell.prototype.is_splittable = function () {
        return false;
    };
    
    UnrecognizedCell.prototype.toJSON = function () {
        /**
         * deepcopy the metadata so copied cells don't share the same object
         */
        return JSON.parse(JSON.stringify(this.data));
    };

    UnrecognizedCell.prototype.fromJSON = function (data) {
        this.data = data;
        if (data.metadata !== undefined) {
            this.metadata = data.metadata;
        } else {
            data.metadata = this.metadata;
        }
        this.element.find('.inner_cell').find("a").text("Unrecognized cell type: " + data.cell_type);
    };
    
    UnrecognizedCell.prototype.create_element = function () {
        Cell.prototype.create_element.apply(this, arguments);
        var cell = this.element = $("<div>").addClass('cell unrecognized_cell');
        cell.attr('tabindex','2');

        var prompt = $('<div/>').addClass('prompt input_prompt');
        cell.append(prompt);
        var inner_cell = $('<div/>').addClass('inner_cell');
        inner_cell.append(
            $("<a>")
                .attr("href", "#")
                .text("Unrecognized cell type")
        );
        cell.append(inner_cell);
        this.element = cell;
    };
    
    UnrecognizedCell.prototype.bind_events = function () {
        Cell.prototype.bind_events.apply(this, arguments);
        var cell = this;
        
        this.element.find('.inner_cell').find("a").click(function () {
            cell.events.trigger('unrecognized_cell.Cell', {cell: cell});
        });
    };

    // Backwards compatibility.
    IPython.Cell = Cell;

    return {
        Cell: Cell,
        UnrecognizedCell: UnrecognizedCell
    };
});
