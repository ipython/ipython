//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// CodeCell
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;
    var key   = IPython.utils.keycodes;

    var CodeCell = function (kernel) {
        this.kernel = kernel;
        this.code_mirror = null;
        this.input_prompt_number = null;
        this.outputs = [];
        this.collapsed = false;
        this.clear_out_timeout = null;
        this.tooltip_on_tab = true;
        IPython.Cell.apply(this, arguments);
    };


    CodeCell.prototype = new IPython.Cell();


    CodeCell.prototype.create_element = function () {
        var cell =  $('<div></div>').addClass('cell border-box-sizing code_cell vbox');
        cell.attr('tabindex','2');
        var input = $('<div></div>').addClass('input hbox');
        input.append($('<div/>').addClass('prompt input_prompt'));
        var input_area = $('<div/>').addClass('input_area box-flex1');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            mode: 'python',
            theme: 'ipython',
            readOnly: this.read_only,
            onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        });
        input.append(input_area);
        var output = $('<div></div>').addClass('output vbox');
        cell.append(input).append(output);
        this.element = cell;
        this.collapse();

        // construct a completer only if class exist
        // otherwise no print view
        if (IPython.Completer != undefined )
        {
        this.completer = new IPython.Completer(this);
        }
    };

    CodeCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress
        // handlers and is used to provide custom key handling. Its return
        // value is used to determine if CodeMirror should ignore the event:
        // true = ignore, false = don't ignore.
        
        if (this.read_only){
            return false;
        }
        
        var that = this;
        // whatever key is pressed, first, cancel the tooltip request before
        // they are sent, and remove tooltip if any, except for tab again
        if(event.type === 'keydown' && event.which != key.tab ) {
            IPython.tooltip.remove_and_cancel_tooltip();
        };

        var cur = editor.getCursor();

        if (event.keyCode === key.enter && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        } else if (event.which === 40 && event.type === 'keypress' && IPython.tooltip.time_before_tooltip >= 0) {
            // triger on keypress (!) otherwise inconsistent event.which depending on plateform
            // browser and keyboard layout !
            // Pressing '(' , request tooltip, don't forget to reappend it
            IPython.tooltip.pending(that);
        } else if (event.which === key.upArrow) {
            // If we are not at the top, let CM handle the up arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_top()) {
                event.stop();
                return false;
            } else {
                return true; 
            };
        } else if (event.which === key.downArrow) {
            // If we are not at the bottom, let CM handle the down arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_bottom()) {
                event.stop();
                return false;
            } else {
                return true; 
            };
        } else if (event.keyCode === key.tab && event.type == 'keydown') {
            // Tab completion.
            //Do not trim here because of tooltip
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur);
            if (pre_cursor.trim() === "") {
                // Don't autocomplete if the part of the line before the cursor
                // is empty.  In this case, let CodeMirror handle indentation.
                return false;
            } else if ((pre_cursor.substr(-1) === "("|| pre_cursor.substr(-1) === " ") && that.tooltip_on_tab ) {
                IPython.tooltip.request(that);
                // Prevent the event from bubbling up.
                event.stop();
                // Prevent CodeMirror from handling the tab.
                return true;
            } else {
                event.stop();
                this.completer.startCompletion();
                return true;
            };
        } else if (event.keyCode === key.backspace && event.type == 'keydown') {
            // If backspace and the line ends with 4 spaces, remove them.
            var line = editor.getLine(cur.line);
            var ending = line.slice(-4);
            if (ending === '    ') {
                editor.replaceRange('',
                    {line: cur.line, ch: cur.ch-4},
                    {line: cur.line, ch: cur.ch}
                );
                event.stop();
                return true;
            } else {
                return false;
            };
        } else {
            // keypress/keyup also trigger on TAB press, and we don't want to
            // use those to disable tab completion.
            return false;
        };
        return false;
    };

    CodeCell.prototype.finish_tooltip = function (reply) {
        IPython.tooltip.show(reply, this);
    };

    // Kernel related calls.

    CodeCell.prototype.execute = function () {
        this.clear_output(true, true, true);
        this.set_input_prompt('*');
        this.element.addClass("running");
        var code = this.get_text();
        var callbacks = {
            'execute_reply': $.proxy(this._handle_execute_reply, this),
            'output': $.proxy(this._handle_output, this),
            'clear_output': $.proxy(this._handle_clear_output, this),
            'cell': this
        };
        var msg_id = this.kernel.execute(this.get_text(), callbacks);
    };


    CodeCell.prototype._handle_execute_reply = function (content) {
        this.set_input_prompt(content.execution_count);
        this.element.removeClass("running");
        // this.dirty = true;
    }


    CodeCell.prototype.request_tooltip = function (func) {
        // Feel free to shorten this logic if you are better
        // than me in regEx
        // basicaly you shoul be able to get xxx.xxx.xxx from 
        // something(range(10), kwarg=smth) ; xxx.xxx.xxx( firstarg, rand(234,23), kwarg1=2, 
        // remove everything between matchin bracket (need to iterate)
        var matchBracket = /\([^\(\)]+\)/g;
        var endBracket = /\([^\(]*$/g;
        var oldfunc = func;

        func = func.replace(matchBracket,"");
        while( oldfunc != func )
        {
        oldfunc = func;
        func = func.replace(matchBracket,"");
        }
        // remove everythin after last open bracket
        func = func.replace(endBracket,"");
        var re = /[a-z_][0-9a-z._]+$/gi; // casse insensitive
        var callbacks = {'object_info_reply': $.proxy(this.finish_tooltip,this)}
        var msg_id = this.kernel.object_info_request(re.exec(func), callbacks);
    };


    // Basic cell manipulation.

    CodeCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.refresh();
        this.code_mirror.focus();
        // We used to need an additional refresh() after the focus, but
        // it appears that this has been fixed in CM. This bug would show
        // up on FF when a newly loaded markdown cell was edited.
    };


    CodeCell.prototype.select_all = function () {
        var start = {line: 0, ch: 0};
        var nlines = this.code_mirror.lineCount();
        var last_line = this.code_mirror.getLine(nlines-1);
        var end = {line: nlines-1, ch: last_line.length};
        this.code_mirror.setSelection(start, end);
    };


    CodeCell.prototype.collapse = function () {
        if (!this.collapsed) {
            this.element.find('div.output').hide();
            this.collapsed = true;
        };
    };


    CodeCell.prototype.expand = function () {
        if (this.collapsed) {
            this.element.find('div.output').show();
            this.collapsed = false;
        };
    };


    CodeCell.prototype.toggle_output = function () {
        if (this.collapsed) {
            this.expand();
        } else {
            this.collapse();
        };
    };


    CodeCell.prototype.set_input_prompt = function (number) {
        this.input_prompt_number = number;
        var ns = number || "&nbsp;";
        this.element.find('div.input_prompt').html('In&nbsp;[' + ns + ']:');
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


    CodeCell.prototype.at_top = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === 0) {
            return true;
        } else {
            return false;
        }
    };


    CodeCell.prototype.at_bottom = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === (this.code_mirror.lineCount()-1)) {
            return true;
        } else {
            return false;
        }
    };


    // Output handling.

    CodeCell.prototype._handle_output = function (msg_type, content) {
        var json = {};
        json.output_type = msg_type;
        if (msg_type === "stream") {
            json.text = content.data;
            json.stream = content.name;
        } else if (msg_type === "display_data") {
            json = this.convert_mime_types(json, content.data);
        } else if (msg_type === "pyout") {
            json.prompt_number = content.execution_count;
            json = this.convert_mime_types(json, content.data);
        } else if (msg_type === "pyerr") {
            json.ename = content.ename;
            json.evalue = content.evalue;
            json.traceback = content.traceback;
        };
        // append with dynamic=true
        this.append_output(json, true);
    };


    CodeCell.prototype.convert_mime_types = function (json, data) {
        if (data['text/plain'] !== undefined) {
            json.text = data['text/plain'];
        };
        if (data['text/html'] !== undefined) {
            json.html = data['text/html'];
        };
        if (data['image/svg+xml'] !== undefined) {
            json.svg = data['image/svg+xml'];
        };
        if (data['image/png'] !== undefined) {
            json.png = data['image/png'];
        };
        if (data['image/jpeg'] !== undefined) {
            json.jpeg = data['image/jpeg'];
        };
        if (data['text/latex'] !== undefined) {
            json.latex = data['text/latex'];
        };
        if (data['application/json'] !== undefined) {
            json.json = data['application/json'];
        };
        if (data['application/javascript'] !== undefined) {
            json.javascript = data['application/javascript'];
        }
        return json;    
    };


    CodeCell.prototype.append_output = function (json, dynamic) {
        // If dynamic is true, javascript output will be eval'd.
        this.expand();
        this.flush_clear_timeout();
        if (json.output_type === 'pyout') {
            this.append_pyout(json, dynamic);
        } else if (json.output_type === 'pyerr') {
            this.append_pyerr(json);
        } else if (json.output_type === 'display_data') {
            this.append_display_data(json, dynamic);
        } else if (json.output_type === 'stream') {
            this.append_stream(json);
        };
        this.outputs.push(json);
    };


    CodeCell.prototype.create_output_area = function () {
        var oa = $("<div/>").addClass("hbox output_area");
        oa.append($('<div/>').addClass('prompt'));
        return oa;
    };


    CodeCell.prototype.append_pyout = function (json, dynamic) {
        var n = json.prompt_number || ' ';
        var toinsert = this.create_output_area();
        toinsert.find('div.prompt').addClass('output_prompt').html('Out[' + n + ']:');
        this.append_mime_type(json, toinsert, dynamic);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ((json.latex !== undefined) || (json.html !== undefined)) {
            this.typeset();
        };
    };


    CodeCell.prototype.append_pyerr = function (json) {
        var tb = json.traceback;
        if (tb !== undefined && tb.length > 0) {
            var s = '';
            var len = tb.length;
            for (var i=0; i<len; i++) {
                s = s + tb[i] + '\n';
            }
            s = s + '\n';
            var toinsert = this.create_output_area();
            this.append_text(s, toinsert);
            this.element.find('div.output').append(toinsert);
        };
    };


    CodeCell.prototype.append_stream = function (json) {
        // temporary fix: if stream undefined (json file written prior to this patch),
        // default to most likely stdout:
        if (json.stream == undefined){
            json.stream = 'stdout';
        }
        if (!utils.fixConsole(json.text)){
            // fixConsole gives nothing (empty string, \r, etc.)
            // so don't append any elements, which might add undesirable space
            return;
        }
        var subclass = "output_"+json.stream;
        if (this.outputs.length > 0){
            // have at least one output to consider
            var last = this.outputs[this.outputs.length-1];
            if (last.output_type == 'stream' && json.stream == last.stream){
                // latest output was in the same stream,
                // so append directly into its pre tag
                // escape ANSI & HTML specials:
                var text = utils.fixConsole(json.text);
                this.element.find('div.'+subclass).last().find('pre').append(text);
                return;
            }
        }
        
        // If we got here, attach a new div
        var toinsert = this.create_output_area();
        this.append_text(json.text, toinsert, "output_stream "+subclass);
        this.element.find('div.output').append(toinsert);
    };


    CodeCell.prototype.append_display_data = function (json, dynamic) {
        var toinsert = this.create_output_area();
        this.append_mime_type(json, toinsert, dynamic);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ( (json.latex !== undefined) || (json.html !== undefined) ) {
            this.typeset();
        };
    };


    CodeCell.prototype.append_mime_type = function (json, element, dynamic) {
        if (json.javascript !== undefined && dynamic) {
            this.append_javascript(json.javascript, element, dynamic);
        } else if (json.html !== undefined) {
            this.append_html(json.html, element);
        } else if (json.latex !== undefined) {
            this.append_latex(json.latex, element);
        } else if (json.svg !== undefined) {
            this.append_svg(json.svg, element);
        } else if (json.png !== undefined) {
            this.append_png(json.png, element);
        } else if (json.jpeg !== undefined) {
            this.append_jpeg(json.jpeg, element);
        } else if (json.text !== undefined) {
            this.append_text(json.text, element);
        };
    };


    CodeCell.prototype.append_html = function (html, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_html rendered_html");
        toinsert.append(html);
        element.append(toinsert);
    };


    CodeCell.prototype.append_javascript = function (js, container) {
        // We just eval the JS code, element appears in the local scope.
        var element = $("<div/>").addClass("box_flex1 output_subarea");
        var kernel = this.kernel;
        container.append(element);
        // Div for js shouldn't be drawn, as it will add empty height to the area.
        container.hide();
        // If the Javascript appends content to `element` that should be drawn, then
        // it must also call `container.show()`.
        eval(js);
    }


    CodeCell.prototype.append_text = function (data, element, extra_class) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_text");
        // escape ANSI & HTML specials in plaintext:
        data = utils.fixConsole(data);
        if (extra_class){
            toinsert.addClass(extra_class);
        }
        toinsert.append($("<pre/>").html(data));
        element.append(toinsert);
    };


    CodeCell.prototype.append_svg = function (svg, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_svg");
        toinsert.append(svg);
        element.append(toinsert);
    };


    CodeCell.prototype.append_png = function (png, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_png");
        toinsert.append($("<img/>").attr('src','data:image/png;base64,'+png));
        element.append(toinsert);
    };


    CodeCell.prototype.append_jpeg = function (jpeg, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_jpeg");
        toinsert.append($("<img/>").attr('src','data:image/jpeg;base64,'+jpeg));
        element.append(toinsert);
    };


    CodeCell.prototype.append_latex = function (latex, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_latex");
        toinsert.append(latex);
        element.append(toinsert);
    };


    CodeCell.prototype._handle_clear_output = function (content) {
        this.clear_output(content.stdout, content.stderr, content.other);
    }


    CodeCell.prototype.clear_output = function (stdout, stderr, other) {
        var that = this;
        if (this.clear_out_timeout != null){
            // fire previous pending clear *immediately*
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        }
        // store flags for flushing the timeout
        this._clear_stdout = stdout;
        this._clear_stderr = stderr;
        this._clear_other = other;
        this.clear_out_timeout = setTimeout(function() {
            // really clear timeout only after a short delay
            // this reduces flicker in 'clear_output; print' cases
            that.clear_out_timeout = null;
            that._clear_stdout = that._clear_stderr = that._clear_other = null;
            that.clear_output_callback(stdout, stderr, other);
        }, 500
        );
    };


    CodeCell.prototype.clear_output_callback = function (stdout, stderr, other) {
        var output_div = this.element.find("div.output");
        
        if (stdout && stderr && other){
            // clear all, no need for logic
            output_div.html("");
            this.outputs = [];
            return;
        }
        // remove html output
        // each output_subarea that has an identifying class is in an output_area
        // which is the element to be removed.
        if (stdout) {
            output_div.find("div.output_stdout").parent().remove();
        }
        if (stderr) {
            output_div.find("div.output_stderr").parent().remove();
        }
        if (other) {
            output_div.find("div.output_subarea").not("div.output_stderr").not("div.output_stdout").parent().remove();
        }
        
        // remove cleared outputs from JSON list:
        for (var i = this.outputs.length - 1; i >= 0; i--) {
            var out = this.outputs[i];
            var output_type = out.output_type;
            if (output_type == "display_data" && other) {
                this.outputs.splice(i,1);
            } else if (output_type == "stream") {
                if (stdout && out.stream == "stdout") {
                    this.outputs.splice(i,1);
                } else if (stderr && out.stream == "stderr") {
                    this.outputs.splice(i,1);
                }
            }
        }
    };


    CodeCell.prototype.flush_clear_timeout = function() {
        var output_div = this.element.find('div.output');
        if (this.clear_out_timeout){
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        };
    }


    // JSON serialization

    CodeCell.prototype.fromJSON = function (data) {
        if (data.cell_type === 'code') {
            if (data.input !== undefined) {
                this.set_text(data.input);
            }
            if (data.prompt_number !== undefined) {
                this.set_input_prompt(data.prompt_number);
            } else {
                this.set_input_prompt();
            };
            var len = data.outputs.length;
            for (var i=0; i<len; i++) {
                // append with dynamic=false.
                this.append_output(data.outputs[i], false);
            };
            if (data.collapsed !== undefined) {
                if (data.collapsed) {
                    this.collapse();
                } else {
                    this.expand();
                };
            };
        };
    };


    CodeCell.prototype.toJSON = function () {
        var data = {};
        data.input = this.get_text();
        data.cell_type = 'code';
        if (this.input_prompt_number) {
            data.prompt_number = this.input_prompt_number;
        };
        var outputs = [];
        var len = this.outputs.length;
        for (var i=0; i<len; i++) {
            outputs[i] = this.outputs[i];
        };
        data.outputs = outputs;
        data.language = 'python';
        data.collapsed = this.collapsed;
        return data;
    };


    IPython.CodeCell = CodeCell;

    return IPython;
}(IPython));
