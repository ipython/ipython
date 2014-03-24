//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CodeCell
//============================================================================
/**
 * An extendable module that provide base functionnality to create cell for notebook.
 * @module IPython
 * @namespace IPython
 * @submodule CodeCell
 */


/* local util for codemirror */
var posEq = function(a, b) {return a.line == b.line && a.ch == b.ch;};

/**
 *
 * function to delete until previous non blanking space character
 * or first multiple of 4 tabstop.
 * @private
 */
CodeMirror.commands.delSpaceToPrevTabStop = function(cm){
    var from = cm.getCursor(true), to = cm.getCursor(false), sel = !posEq(from, to);
    if (!posEq(from, to)) { cm.replaceRange("", from, to); return; }
    var cur = cm.getCursor(), line = cm.getLine(cur.line);
    var tabsize = cm.getOption('tabSize');
    var chToPrevTabStop = cur.ch-(Math.ceil(cur.ch/tabsize)-1)*tabsize;
    from = {ch:cur.ch-chToPrevTabStop,line:cur.line};
    var select = cm.getRange(from,cur);
    if( select.match(/^\ +$/) !== null){
        cm.replaceRange("",from,cur);
    } else {
        cm.deleteH(-1,"char");
    }
};


var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;
    var keycodes = IPython.keyboard.keycodes;

    /**
     * A Cell conceived to write code.
     *
     * The kernel doesn't have to be set at creation time, in that case
     * it will be null and set_kernel has to be called later.
     * @class CodeCell
     * @extends IPython.Cell
     *
     * @constructor
     * @param {Object|null} kernel
     * @param {object|undefined} [options]
     *      @param [options.cm_config] {object} config to pass to CodeMirror
     */
    var CodeCell = function (kernel, options) {
        this.kernel = kernel || null;
        this.collapsed = false;

        // create all attributed in constructor function
        // even if null for V8 VM optimisation
        this.input_prompt_number = null;
        this.celltoolbar = null;
        this.output_area = null;
        this.last_msg_id = null;
        this.completer = null;


        var cm_overwrite_options  = {
            onKeyEvent: $.proxy(this.handle_keyevent,this)
        };

        options = this.mergeopt(CodeCell, options, {cm_config:cm_overwrite_options});

        IPython.Cell.apply(this,[options]);

        // Attributes we want to override in this subclass.
        this.cell_type = "code";

        var that = this;
        this.element.focusout(
            function() { that.auto_highlight(); }
        );
    };

    CodeCell.options_default = {
        cm_config : {
            extraKeys: {
                "Tab" :  "indentMore",
                "Shift-Tab" : "indentLess",
                "Backspace" : "delSpaceToPrevTabStop",
                "Cmd-/" : "toggleComment",
                "Ctrl-/" : "toggleComment"
            },
            mode: 'ipython',
            theme: 'ipython',
            matchBrackets: true,
             // don't auto-close strings because of CodeMirror #2385
            autoCloseBrackets: "()[]{}"
        }
    };

    CodeCell.msg_cells = {};

    CodeCell.prototype = new IPython.Cell();

    /**
     * @method auto_highlight
     */
    CodeCell.prototype.auto_highlight = function () {
        this._auto_highlight(IPython.config.cell_magic_highlight);
    };

    /** @method create_element */
    CodeCell.prototype.create_element = function () {
        IPython.Cell.prototype.create_element.apply(this, arguments);

        var cell =  $('<div></div>').addClass('cell border-box-sizing code_cell');
        cell.attr('tabindex','2');

        var input = $('<div></div>').addClass('input');
        var prompt = $('<div/>').addClass('prompt input_prompt');
        var inner_cell = $('<div/>').addClass('inner_cell');
        this.celltoolbar = new IPython.CellToolbar(this);
        inner_cell.append(this.celltoolbar.element);
        var input_area = $('<div/>').addClass('input_area');
        this.code_mirror = CodeMirror(input_area.get(0), this.cm_config);
        $(this.code_mirror.getInputField()).attr("spellcheck", "false");
        inner_cell.append(input_area);
        input.append(prompt).append(inner_cell);

        var widget_area = $('<div/>')
            .addClass('widget-area')
            .hide();
        this.widget_area = widget_area;
        var widget_prompt = $('<div/>')
            .addClass('prompt')
            .appendTo(widget_area);
        var widget_subarea = $('<div/>')
            .addClass('widget-subarea')
            .appendTo(widget_area);
        this.widget_subarea = widget_subarea;
        var widget_clear_buton = $('<button />')
            .addClass('close')
            .html('&times;')
            .click(function() {
                widget_area.slideUp('', function(){ widget_subarea.html(''); });
                })
            .appendTo(widget_prompt);

        var output = $('<div></div>');
        cell.append(input).append(widget_area).append(output);
        this.element = cell;
        this.output_area = new IPython.OutputArea(output, true);
        this.completer = new IPython.Completer(this);
    };

    /** @method bind_events */
    CodeCell.prototype.bind_events = function () {
        IPython.Cell.prototype.bind_events.apply(this);
        var that = this;

        this.element.focusout(
            function() { that.auto_highlight(); }
        );
    };


    /**
     *  This method gets called in CodeMirror's onKeyDown/onKeyPress
     *  handlers and is used to provide custom key handling. Its return
     *  value is used to determine if CodeMirror should ignore the event:
     *  true = ignore, false = don't ignore.
     *  @method handle_codemirror_keyevent
     */
    CodeCell.prototype.handle_codemirror_keyevent = function (editor, event) {

        var that = this;
        // whatever key is pressed, first, cancel the tooltip request before
        // they are sent, and remove tooltip if any, except for tab again
        var tooltip_closed = null;
        if (event.type === 'keydown' && event.which != keycodes.tab ) {
            tooltip_closed = IPython.tooltip.remove_and_cancel_tooltip();
        }

        var cur = editor.getCursor();
        if (event.keyCode === keycodes.enter){
            this.auto_highlight();
        }

        if (event.which === keycodes.down && event.type === 'keypress' && IPython.tooltip.time_before_tooltip >= 0) {
            // triger on keypress (!) otherwise inconsistent event.which depending on plateform
            // browser and keyboard layout !
            // Pressing '(' , request tooltip, don't forget to reappend it
            // The second argument says to hide the tooltip if the docstring
            // is actually empty
            IPython.tooltip.pending(that, true);
        } else if ( tooltip_closed && event.which === keycodes.esc && event.type === 'keydown') {
            // If tooltip is active, cancel it.  The call to
            // remove_and_cancel_tooltip above doesn't pass, force=true.
            // Because of this it won't actually close the tooltip
            // if it is in sticky mode. Thus, we have to check again if it is open
            // and close it with force=true.
            if (!IPython.tooltip._hidden) {
                IPython.tooltip.remove_and_cancel_tooltip(true);
            }
            // If we closed the tooltip, don't let CM or the global handlers
            // handle this event.
            event.stop();
            return true;
        } else if (event.keyCode === keycodes.tab && event.type === 'keydown' && event.shiftKey) {
                if (editor.somethingSelected()){
                    var anchor = editor.getCursor("anchor");
                    var head = editor.getCursor("head");
                    if( anchor.line != head.line){
                        return false;
                    }
                }
                IPython.tooltip.request(that);
                event.stop();
                return true;
        } else if (event.keyCode === keycodes.tab && event.type == 'keydown') {
            // Tab completion.
            IPython.tooltip.remove_and_cancel_tooltip();
            if (editor.somethingSelected()) {
                return false;
            }
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur);
            if (pre_cursor.trim() === "") {
                // Don't autocomplete if the part of the line before the cursor
                // is empty.  In this case, let CodeMirror handle indentation.
                return false;
            } else {
                event.stop();
                this.completer.startCompletion();
                return true;
            }
        } 
        
        // keyboard event wasn't one of those unique to code cells, let's see
        // if it's one of the generic ones (i.e. check edit mode shortcuts)
        return IPython.Cell.prototype.handle_codemirror_keyevent.apply(this, [editor, event]);
    };

    // Kernel related calls.

    CodeCell.prototype.set_kernel = function (kernel) {
        this.kernel = kernel;
    };

    /**
     * Execute current code cell to the kernel
     * @method execute
     */
    CodeCell.prototype.execute = function () {
        this.output_area.clear_output();
        
        // Clear widget area
        this.widget_subarea.html('');
        this.widget_subarea.height('');
        this.widget_area.height('');
        this.widget_area.hide();

        this.set_input_prompt('*');
        this.element.addClass("running");
        if (this.last_msg_id) {
            this.kernel.clear_callbacks_for_msg(this.last_msg_id);
        }
        var callbacks = this.get_callbacks();
        
        var old_msg_id = this.last_msg_id;
        this.last_msg_id = this.kernel.execute(this.get_text(), callbacks, {silent: false, store_history: true});
        if (old_msg_id) {
            delete CodeCell.msg_cells[old_msg_id];
        }
        CodeCell.msg_cells[this.last_msg_id] = this;
    };
    
    /**
     * Construct the default callbacks for
     * @method get_callbacks
     */
    CodeCell.prototype.get_callbacks = function () {
        return {
            shell : {
                reply : $.proxy(this._handle_execute_reply, this),
                payload : {
                    set_next_input : $.proxy(this._handle_set_next_input, this),
                    page : $.proxy(this._open_with_pager, this)
                }
            },
            iopub : {
                output : $.proxy(this.output_area.handle_output, this.output_area),
                clear_output : $.proxy(this.output_area.handle_clear_output, this.output_area),
            },
            input : $.proxy(this._handle_input_request, this)
        };
    };
    
    CodeCell.prototype._open_with_pager = function (payload) {
        $([IPython.events]).trigger('open_with_text.Pager', payload);
    };

    /**
     * @method _handle_execute_reply
     * @private
     */
    CodeCell.prototype._handle_execute_reply = function (msg) {
        this.set_input_prompt(msg.content.execution_count);
        this.element.removeClass("running");
        $([IPython.events]).trigger('set_dirty.Notebook', {value: true});
    };

    /**
     * @method _handle_set_next_input
     * @private
     */
    CodeCell.prototype._handle_set_next_input = function (payload) {
        var data = {'cell': this, 'text': payload.text};
        $([IPython.events]).trigger('set_next_input.Notebook', data);
    };

    /**
     * @method _handle_input_request
     * @private
     */
    CodeCell.prototype._handle_input_request = function (msg) {
        this.output_area.append_raw_input(msg);
    };


    // Basic cell manipulation.

    CodeCell.prototype.select = function () {
        var cont = IPython.Cell.prototype.select.apply(this);
        if (cont) {
            this.code_mirror.refresh();
            this.auto_highlight();
        }
        return cont;
    };

    CodeCell.prototype.render = function () {
        var cont = IPython.Cell.prototype.render.apply(this);
        // Always execute, even if we are already in the rendered state
        return cont;
    };
    
    CodeCell.prototype.unrender = function () {
        // CodeCell is always rendered
        return false;
    };

    CodeCell.prototype.select_all = function () {
        var start = {line: 0, ch: 0};
        var nlines = this.code_mirror.lineCount();
        var last_line = this.code_mirror.getLine(nlines-1);
        var end = {line: nlines-1, ch: last_line.length};
        this.code_mirror.setSelection(start, end);
    };


    CodeCell.prototype.collapse_output = function () {
        this.collapsed = true;
        this.output_area.collapse();
    };


    CodeCell.prototype.expand_output = function () {
        this.collapsed = false;
        this.output_area.expand();
        this.output_area.unscroll_area();
    };

    CodeCell.prototype.scroll_output = function () {
        this.output_area.expand();
        this.output_area.scroll_if_long();
    };

    CodeCell.prototype.toggle_output = function () {
        this.collapsed = Boolean(1 - this.collapsed);
        this.output_area.toggle_output();
    };

    CodeCell.prototype.toggle_output_scroll = function () {
        this.output_area.toggle_scroll();
    };


    CodeCell.input_prompt_classical = function (prompt_value, lines_number) {
        var ns;
        if (prompt_value === undefined) {
            ns = "&nbsp;";
        } else {
            ns = encodeURIComponent(prompt_value);
        }
        return 'In&nbsp;[' + ns + ']:';
    };

    CodeCell.input_prompt_continuation = function (prompt_value, lines_number) {
        var html = [CodeCell.input_prompt_classical(prompt_value, lines_number)];
        for(var i=1; i < lines_number; i++) {
            html.push(['...:']);
        }
        return html.join('<br/>');
    };

    CodeCell.input_prompt_function = CodeCell.input_prompt_classical;


    CodeCell.prototype.set_input_prompt = function (number) {
        var nline = 1;
        if (this.code_mirror !== undefined) {
           nline = this.code_mirror.lineCount();
        }
        this.input_prompt_number = number;
        var prompt_html = CodeCell.input_prompt_function(this.input_prompt_number, nline);
        // This HTML call is okay because the user contents are escaped.
        this.element.find('div.input_prompt').html(prompt_html);
    };


    CodeCell.prototype.clear_input = function () {
        this.code_mirror.setValue('');
    };


    CodeCell.prototype.get_text = function () {
        return this.code_mirror.getValue();
    };


    CodeCell.prototype.set_text = function (code) {
        return this.code_mirror.setValue(code);
    };


    CodeCell.prototype.clear_output = function (wait) {
        this.output_area.clear_output(wait);
        this.set_input_prompt();
    };


    // JSON serialization

    CodeCell.prototype.fromJSON = function (data) {
        IPython.Cell.prototype.fromJSON.apply(this, arguments);
        if (data.cell_type === 'code') {
            if (data.input !== undefined) {
                this.set_text(data.input);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                this.code_mirror.clearHistory();
                this.auto_highlight();
            }
            if (data.prompt_number !== undefined) {
                this.set_input_prompt(data.prompt_number);
            } else {
                this.set_input_prompt();
            }
            this.output_area.trusted = data.trusted || false;
            this.output_area.fromJSON(data.outputs);
            if (data.collapsed !== undefined) {
                if (data.collapsed) {
                    this.collapse_output();
                } else {
                    this.expand_output();
                }
            }
        }
    };


    CodeCell.prototype.toJSON = function () {
        var data = IPython.Cell.prototype.toJSON.apply(this);
        data.input = this.get_text();
        // is finite protect against undefined and '*' value
        if (isFinite(this.input_prompt_number)) {
            data.prompt_number = this.input_prompt_number;
        }
        var outputs = this.output_area.toJSON();
        data.outputs = outputs;
        data.language = 'python';
        data.trusted = this.output_area.trusted;
        data.collapsed = this.collapsed;
        return data;
    };

    /**
     * handle cell level logic when a cell is unselected
     * @method unselect
     * @return is the action being taken
     */
    CodeCell.prototype.unselect = function () {
        var cont = IPython.Cell.prototype.unselect.apply(this);
        if (cont) {
            // When a code cell is usnelected, make sure that the corresponding
            // tooltip and completer to that cell is closed.
            IPython.tooltip.remove_and_cancel_tooltip(true);
            if (this.completer !== null) {
                this.completer.close();
            }
        }
        return cont;
    };

    IPython.CodeCell = CodeCell;

    return IPython;
}(IPython));
