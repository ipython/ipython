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

    var CodeCell = function (notebook) {
        this.code_mirror = null;
        this.input_prompt_number = null;
        this.completion_cursor = null;
        this.outputs = [];
        this.collapsed = false;
        this.tooltip_timeout = null;
        this.clear_out_timeout = null;
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

        // construct a completer
        // And give it the function to call to get the completion list
        var that = this;
        this.completer = new IPython.Completer(this.code_mirror,function(callback){that.requestCompletion(callback)});
    };

    //TODO, try to diminish the number of parameters.
    CodeCell.prototype.request_tooltip_after_time = function (pre_cursor,time){
        var that = this;
        if (pre_cursor === "" || pre_cursor === "(" ) {
            // don't do anything if line beggin with '(' or is empty
        } else {
            // Will set a timer to request tooltip in `time`
            that.tooltip_timeout = setTimeout(function(){
                    IPython.notebook.request_tool_tip(that, pre_cursor)
                },time);
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
        
        // note that we are comparing and setting the time to wait at each key press.
        // a better wqy might be to generate a new function on each time change and
        // assign it to CodeCell.prototype.request_tooltip_after_time
        var tooltip_wait_time = this.notebook.time_before_tooltip;
        var tooltip_on_tab    = this.notebook.tooltip_on_tab;
        var that = this;
        // whatever key is pressed, first, cancel the tooltip request before
        // they are sent, and remove tooltip if any
        if(event.type === 'keydown' ) {
            that.remove_and_cancel_tooltip();
        };


        if (event.keyCode === key.enter && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        } else if (event.which === 40 && event.type === 'keypress' && tooltip_wait_time >= 0) {
            // triger aon keypress (!) otherwise inconsistent event.which depending on plateform
            // browser and keyboard layout !
            // Pressing '(' , request tooltip, don't forget to reappend it
            var cursor = editor.getCursor();
            var pre_cursor = editor.getRange({line:cursor.line,ch:0},cursor).trim()+'(';
            that.request_tooltip_after_time(pre_cursor,tooltip_wait_time);
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
            var cur = editor.getCursor();
            //Do not trim here because of tooltip
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur);
            if (pre_cursor.trim() === "") {
                // Don't autocomplete if the part of the line before the cursor
                // is empty.  In this case, let CodeMirror handle indentation.
                return false;
            } else if ((pre_cursor.substr(-1) === "("|| pre_cursor.substr(-1) === " ") && tooltip_on_tab ) {
                that.request_tooltip_after_time(pre_cursor,0);
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
            var cur = editor.getCursor();
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

    CodeCell.prototype.remove_and_cancel_tooltip = function() {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        if (this.tooltip_timeout != null){
            clearTimeout(this.tooltip_timeout);
            $('#tooltip').remove();
            this.tooltip_timeout = null;
        }
    }

    CodeCell.prototype.finish_tooltip = function (reply) {
        // Extract call tip data; the priority is call, init, main.
        defstring = reply.call_def;
        if (defstring == null) { defstring = reply.init_definition; }
        if (defstring == null) { defstring = reply.definition; }

        docstring = reply.call_docstring;
        if (docstring == null) { docstring = reply.init_docstring; }
        if (docstring == null) { docstring = reply.docstring; }
        if (docstring == null) { docstring = "<empty docstring>"; }

        name=reply.name;

        var that = this;
        var tooltip = $('<div/>').attr('id', 'tooltip').addClass('tooltip');
        // remove to have the tooltip not Limited in X and Y
        tooltip.addClass('smalltooltip');
        var pre=$('<pre/>').html(utils.fixConsole(docstring));
        var expandlink=$('<a/>').attr('href',"#");
            expandlink.addClass("ui-corner-all"); //rounded corner
            expandlink.attr('role',"button");
            //expandlink.addClass('ui-button');
            //expandlink.addClass('ui-state-default');
        var expandspan=$('<span/>').text('Expand');
            expandspan.addClass('ui-icon');
            expandspan.addClass('ui-icon-plus');
        expandlink.append(expandspan);
        expandlink.attr('id','expanbutton');
        expandlink.click(function(){
            tooltip.removeClass('smalltooltip');
            tooltip.addClass('bigtooltip');
            $('#expanbutton').remove();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        });
        var morelink=$('<a/>').attr('href',"#");
            morelink.attr('role',"button");
            morelink.addClass('ui-button');
            //morelink.addClass("ui-corner-all"); //rounded corner
            //morelink.addClass('ui-state-default');
        var morespan=$('<span/>').text('Open in Pager');
            morespan.addClass('ui-icon');
            morespan.addClass('ui-icon-arrowstop-l-n');
        morelink.append(morespan);
        morelink.click(function(){
            var msg_id = IPython.notebook.kernel.execute(name+"?");
            IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        });

        var closelink=$('<a/>').attr('href',"#");
            closelink.attr('role',"button");
            closelink.addClass('ui-button');
            //closelink.addClass("ui-corner-all"); //rounded corner
            //closelink.adClass('ui-state-default'); // grey background and blue cross
        var closespan=$('<span/>').text('Close');
            closespan.addClass('ui-icon');
            closespan.addClass('ui-icon-close');
        closelink.append(closespan);
        closelink.click(function(){
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
            });
        //construct the tooltip
        tooltip.append(closelink);
        tooltip.append(expandlink);
        tooltip.append(morelink);
        if(defstring){
            defstring_html = $('<pre/>').html(utils.fixConsole(defstring));
            tooltip.append(defstring_html);
        }
        tooltip.append(pre);
        var pos = this.code_mirror.cursorCoords();
        tooltip.css('left',pos.x+'px');
        tooltip.css('top',pos.yBot+'px');
        $('body').append(tooltip);

        // issues with cross-closing if multiple tooltip in less than 5sec
        // keep it comented for now
        // setTimeout(that.remove_and_cancel_tooltip, 5000);
    };

    // As you type completer
    // this should be called by the completer, that in return will
    // be reclled by finish_completing
    CodeCell.prototype.requestCompletion= function(callback)
    {
        this._compcallback = callback;
        var cur = this.code_mirror.getCursor();
        var pre_cursor = this.code_mirror.getRange({line:cur.line,ch:0},cur);
        pre_cursor.trim();
        // Autocomplete the current line.
        var line = this.code_mirror.getLine(cur.line);
        // one could fork here and directly call finish completing
        // if kernel is busy
        IPython.notebook.complete_cell(this, line, cur.ch);
    }

    // called when completion came back from the kernel. this will inspect the
    // curent cell for (more) completion merge the resuults with the ones
    // comming from the kernel and forward it to the completer
    CodeCell.prototype.finish_completing = function (matched_text, matches) {
        // let's build a function that wrap all that stuff into what is needed for the
        // new completer:
        //
        var cur = this.code_mirror.getCursor();
        var res = CodeMirror.contextHint(this.code_mirror);
        
        // append the introspection result, in order, at
        // at the beginning of the table and compute the replacement rance
        // from current cursor positon and matched_text length.
        for(var i= matches.length-1; i>=0 ;--i)
        {
            res.unshift(
                {
                    str  : matches[i],
                    type : "introspection",
                    from : {line: cur.line, ch: cur.ch-matched_text.length},
                    to   : {line: cur.line, ch: cur.ch}
                }
            )
        }
        this._compcallback(res);
    };


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
        this.clear_out_timeout = setTimeout(function(){
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
        if (stdout){
            output_div.find("div.output_stdout").parent().remove();
        }
        if (stderr){
            output_div.find("div.output_stderr").parent().remove();
        }
        if (other){
            output_div.find("div.output_subarea").not("div.output_stderr").not("div.output_stdout").parent().remove();
        }
        
        // remove cleared outputs from JSON list:
        for (var i = this.outputs.length - 1; i >= 0; i--){
            var out = this.outputs[i];
            var output_type = out.output_type;
            if (output_type == "display_data" && other){
                this.outputs.splice(i,1);
            }else if (output_type == "stream"){
                if (stdout && out.stream == "stdout"){
                    this.outputs.splice(i,1);
                }else if (stderr && out.stream == "stderr"){
                    this.outputs.splice(i,1);
                }
            }
        }
    };


    CodeCell.prototype.clear_input = function () {
        this.code_mirror.setValue('');
    };
    
    CodeCell.prototype.flush_clear_timeout = function() {
        var output_div = this.element.find('div.output');
        if (this.clear_out_timeout){
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        };
    }


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
