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
        this.input_prompt_number = ' ';
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
            onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        });
        input.append(input_area);
        var output = $('<div></div>').addClass('output vbox');
        cell.append(input).append(output);
        this.element = cell;
        this.collapse()
    };


    CodeCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress handlers and
        // is used to provide custom key handling. Its return value is used to determine
        // if CodeMirror should ignore the event: true = ignore, false = don't ignore.
        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        } else if (event.keyCode === 9 && event.type == 'keydown') {
            // Tab completion.
            var cur = editor.getCursor();
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur).trim();
            if (pre_cursor === "") {
                // Don't autocomplete if the part of the line before the cursor is empty.
                // In this case, let CodeMirror handle indentation.
                return false;
            } else {
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
            };
        } else {
            // keypress/keyup also trigger on TAB press, and we don't want to use those
            // to disable tab completion.
            if (this.is_completing && event.keyCode !== 9) {
                var ed_cur = editor.getCursor();
                var cc_cur = this.completion_cursor;
                if (ed_cur.line !== cc_cur.line || ed_cur.ch !== cc_cur.ch) {
                    this.is_completing = false;
                    this.completion_cursor = null;
                };
            };
            return false;
        };
    };


    CodeCell.prototype.finish_completing = function (matched_text, matches) {
        // console.log("Got matches", matched_text, matches);
        if (!this.is_completing || matches.length === 0) {return;}

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
        if (json.latex !== undefined) {
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
        var toinsert = this.create_output_area();
        this.append_text(json.text, toinsert);
        this.element.find('div.output').append(toinsert);
    };


    CodeCell.prototype.append_display_data = function (json) {
        var toinsert = this.create_output_area();
        this.append_mime_type(json, toinsert)
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if (json.latex !== undefined) {
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
    }


    CodeCell.prototype.append_text = function (data, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_stream");
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
    }


    CodeCell.prototype.clear_output = function () {
        this.element.find("div.output").html("");
        this.outputs = [];
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
        var n = number || ' ';
        this.input_prompt_number = n
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
        // console.log('Import from JSON:', data);
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
            data.prompt_number = this.input_prompt_number
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

