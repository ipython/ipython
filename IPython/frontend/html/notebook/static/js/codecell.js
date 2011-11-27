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

    var utils = IPython.utils;

    var CodeCell = function (notebook) {
        this.code_mirror = null;
        this.input_prompt_number = '&nbsp;';
        this.is_completing = false;
        this.completion_cursor = null;
        this.outputs = [];
        this.collapsed = false;
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
    };

    //TODO, try to diminish the number of parameters.
    CodeCell.prototype.request_tooltip_after_time = function (pre_cursor,time,that){
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

        // note that we are comparing and setting the time to wait at each key press.
        // a better wqy might be to generate a new function on each time change and
        // assign it to CodeCell.prototype.request_tooltip_after_time
        tooltip_wait_time = this.notebook.time_before_tooltip;
        tooltip_on_tab    = this.notebook.tooltip_on_tab;
        var that = this;
        // whatever key is pressed, first, cancel the tooltip request before
        // they are sent, and remove tooltip if any
        if(event.type === 'keydown' && this.tooltip_timeout != null){
            CodeCell.prototype.remove_and_cancell_tooltip(that.tooltip_timeout);
            that.tooltip_timeout=null;
        }

        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        }else if (event.which === 40 && event.type === 'keypress' && tooltip_wait_time >= 0) {
            // triger aon keypress (!) otherwise inconsistent event.which depending on plateform
            // browser and keyboard layout !
            // Pressing '(' , request tooltip, don't forget to reappend it
            var cursor = editor.getCursor();
            var pre_cursor = editor.getRange({line:cursor.line,ch:0},cursor).trim()+'(';
            CodeCell.prototype.request_tooltip_after_time(pre_cursor,tooltip_wait_time,that);
        } else if (event.keyCode === 9 && event.type == 'keydown') {
            // Tab completion.
            var cur = editor.getCursor();
            //Do not trim here because of tooltip
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur);
            if (pre_cursor.trim() === "") {
                // Don't autocomplete if the part of the line before the cursor
                // is empty.  In this case, let CodeMirror handle indentation.
                return false;
            } else if ((pre_cursor.substr(-1) === "("|| pre_cursor.substr(-1) === " ") && tooltip_on_tab ) {
                CodeCell.prototype.request_tooltip_after_time(pre_cursor,0,that);
            } else {
                pre_cursor.trim();
                // Autocomplete the current line.
                event.stop();
                var line = editor.getLine(cur.line);
                this.is_completing = true;
                this.completion_cursor = cur;
                IPython.notebook.complete_cell(this, line, cur.ch);
                return true;
            }
        } else if (event.keyCode === 8 && event.type == 'keydown') {
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
            }
        } else if (event.keyCode === 76 && event.ctrlKey && event.shiftKey
                   && event.type == 'keydown') {
            // toggle line numbers with Ctrl-Shift-L
            this.toggle_line_numbers();
        }
        else {
            // keypress/keyup also trigger on TAB press, and we don't want to
            // use those to disable tab completion.
            if (this.is_completing && event.keyCode !== 9) {
                var ed_cur = editor.getCursor();
                var cc_cur = this.completion_cursor;
                if (ed_cur.line !== cc_cur.line || ed_cur.ch !== cc_cur.ch) {
                    this.is_completing = false;
                    this.completion_cursor = null;
                }
            }
            return false;
        };
        return false;
    };

    CodeCell.prototype.remove_and_cancell_tooltip = function(timeout)
    {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        clearTimeout(timeout);
        $('#tooltip').remove();
    }

    CodeCell.prototype.finish_tooltip = function (reply) {
        defstring=reply.definition;
        docstring=reply.docstring;
        if(docstring == null){docstring="<empty docstring>"};
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
            IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.selected_cell().cell_id;
            CodeCell.prototype.remove_and_cancell_tooltip(that.tooltip_timeout);
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
            CodeCell.prototype.remove_and_cancell_tooltip(that.tooltip_timeout);
            setTimeout(function(){that.code_mirror.focus();}, 50);
            });
        //construct the tooltip
        tooltip.append(closelink);
        tooltip.append(expandlink);
        tooltip.append(morelink);
        if(defstring){
            defstring_html= $('<pre/>').html(utils.fixConsole(defstring));
            tooltip.append(defstring_html);
        }
        tooltip.append(pre);
        var pos = this.code_mirror.cursorCoords();
        tooltip.css('left',pos.x+'px');
        tooltip.css('top',pos.yBot+'px');
        $('body').append(tooltip);

        // issues with cross-closing if multiple tooltip in less than 5sec
        // keep it comented for now
        // setTimeout(CodeCell.prototype.remove_and_cancell_tooltip, 5000);
    };


    CodeCell.prototype.finish_completing = function (matched_text, matches) {
        // console.log("Got matches", matched_text, matches);
        var newm = new Array();
        if(this.notebook.smart_completer)
        {
            kwargs = new Array();
            other = new Array();
            for(var i=0;i<matches.length; ++i){
                if(matches[i].substr(-1) === '='){
                    kwargs.push(matches[i]);
                }else{other.push(matches[i]);}
            }
            newm = kwargs.concat(other);
            matches=newm;
        }
        if (!this.is_completing || matches.length === 0) {return;}

        //try to check if the user is typing tab at least twice after a word
        // and completion is "done"
        fallback_on_tooltip_after=2
        if(matches.length==1 && matched_text === matches[0])
        {
            if(this.npressed >fallback_on_tooltip_after  && this.prevmatch==matched_text)
            {
                console.log('Ok, you really want to complete after pressing tab '+this.npressed+' times !');
                console.log('You should understand that there is no (more) completion for that !');
                console.log("I'll show you the tooltip, will you stop bothering me ?");
                this.request_tooltip_after_time(matched_text+'(',0,this);
                return;
            }
            this.prevmatch=matched_text
            this.npressed=this.npressed+1;
        }
        else
        {
            this.prevmatch="";
            this.npressed=0;
        }

        var that = this;
        var cur = this.completion_cursor;

        var insert = function (selected_text) {
            that.code_mirror.replaceRange(
                selected_text,
                {line: cur.line, ch: (cur.ch-matched_text.length)},
                {line: cur.line, ch: cur.ch}
            );
        };

        if (matches.length === 1) {
            insert(matches[0]);
            setTimeout(function(){that.code_mirror.focus();}, 50);
            return;
        };

        var complete = $('<div/>').addClass('completions');
        var select = $('<select/>').attr('multiple','true');
        for (var i=0; i<matches.length; ++i) {
            select.append($('<option/>').text(matches[i]));
        }
        select.children().first().attr('selected','true');
        select.attr('size',Math.min(10,matches.length));
        var pos = this.code_mirror.cursorCoords();
        complete.css('left',pos.x+'px');
        complete.css('top',pos.yBot+'px');
        complete.append(select);

        $('body').append(complete);
        var done = false;

        var close = function () {
            if (done) return;
            done = true;
            complete.remove();
            that.is_completing = false;
            that.completion_cursor = null;
        };

        var pick = function () {
            insert(select.val()[0]);
            close();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        };

        select.blur(close);
        select.keydown(function (event) {
            var code = event.which;
            if (code === 13 || code === 32) {
                // Pressing SPACE or ENTER will cause a pick
                event.stopPropagation();
                event.preventDefault();
                pick();
            } else if (code === 38 || code === 40) {
                // We don't want the document keydown handler to handle UP/DOWN,
                // but we want the default action.
                event.stopPropagation();
            } else {
                // All other key presses exit completion.
                event.stopPropagation();
                event.preventDefault();
                close();
                that.code_mirror.focus();
            }
        });
        // Double click also causes a pick.
        select.dblclick(pick);
        select.focus();
    };

    CodeCell.prototype.toggle_line_numbers = function () {
        if (this.code_mirror.getOption('lineNumbers') == false) {
            this.code_mirror.setOption('lineNumbers', true);
        } else {
            this.code_mirror.setOption('lineNumbers', false);
        }
        this.code_mirror.refresh();
    };

    CodeCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        // Todo: this dance is needed because as of CodeMirror 2.12, focus is
        // not causing the cursor to blink if the editor is empty initially.
        // While this seems to fix the issue, this should be fixed
        // in CodeMirror proper.
        var s = this.code_mirror.getValue();
        this.code_mirror.focus();
        if (s === '') this.code_mirror.setValue('');
    };


    CodeCell.prototype.select_all = function () {
        var start = {line: 0, ch: 0};
        var nlines = this.code_mirror.lineCount();
        var last_line = this.code_mirror.getLine(nlines-1);
        var end = {line: nlines-1, ch: last_line.length};
        this.code_mirror.setSelection(start, end);
    };


    CodeCell.prototype.append_output = function (json) {
        this.expand();
        if (json.output_type === 'pyout') {
            this.append_pyout(json);
        } else if (json.output_type === 'pyerr') {
            this.append_pyerr(json);
        } else if (json.output_type === 'display_data') {
            this.append_display_data(json);
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


    CodeCell.prototype.append_pyout = function (json) {
        n = json.prompt_number || ' ';
        var toinsert = this.create_output_area();
        toinsert.find('div.prompt').addClass('output_prompt').html('Out[' + n + ']:');
        this.append_mime_type(json, toinsert);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ((json.latex !== undefined) || (json.html !== undefined)) {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
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
        var subclass = "output_"+json.stream;
        if (this.outputs.length > 0){
            // have at least one output to consider
            var last = this.outputs[this.outputs.length-1];
            if (last.output_type == 'stream' && json.stream == last.stream){
                // latest output was in the same stream,
                // so append directly into its pre tag
                this.element.find('div.'+subclass).last().find('pre').append(json.text);
                return;
            }
        }
        
        // If we got here, attach a new div
        var toinsert = this.create_output_area();
        this.append_text(json.text, toinsert, "output_stream "+subclass);
        this.element.find('div.output').append(toinsert);
    };


    CodeCell.prototype.append_display_data = function (json) {
        var toinsert = this.create_output_area();
        this.append_mime_type(json, toinsert);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ( (json.latex !== undefined) || (json.html !== undefined) ) {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        };
    };


    CodeCell.prototype.append_mime_type = function (json, element) {
        if (json.html !== undefined) {
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


    CodeCell.prototype.append_text = function (data, element, extra_class) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_text");
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
        var n = number || '&nbsp;';
        this.input_prompt_number = n;
        this.element.find('div.input_prompt').html('In&nbsp;[' + n + ']:');
    };


    CodeCell.prototype.get_code = function () {
        return this.code_mirror.getValue();
    };


    CodeCell.prototype.set_code = function (code) {
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
        console.log('Import from JSON:', data);
        if (data.cell_type === 'code') {
            if (data.input !== undefined) {
                this.set_code(data.input);
            }
            if (data.prompt_number !== undefined) {
                this.set_input_prompt(data.prompt_number);
            } else {
                this.set_input_prompt();
            };
            var len = data.outputs.length;
            for (var i=0; i<len; i++) {
                this.append_output(data.outputs[i]);
            };
            if (data.collapsed !== undefined) {
                if (data.collapsed) {
                    this.collapse();
                };
            };
        };
    };


    CodeCell.prototype.toJSON = function () {
        var data = {};
        data.input = this.get_code();
        data.cell_type = 'code';
        if (this.input_prompt_number !== ' ') {
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
        // console.log('Export to JSON:',data);
        return data;
    };


    IPython.CodeCell = CodeCell;

    return IPython;
}(IPython));
