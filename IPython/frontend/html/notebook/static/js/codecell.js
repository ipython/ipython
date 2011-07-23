
//============================================================================
// CodeCell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var CodeCell = function (notebook) {
        this.code_mirror = null;
        this.input_prompt_number = ' ';
        IPython.Cell.apply(this, arguments);
    };


    CodeCell.prototype = new IPython.Cell();


    CodeCell.prototype.create_element = function () {
        var cell =  $('<div></div>').addClass('cell border-box-sizing code_cell vbox');
        var input = $('<div></div>').addClass('input hbox');
        input.append($('<div/>').addClass('prompt input_prompt'));
        var input_area = $('<div/>').addClass('input_area box-flex1');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            enterMode : 'flat',
            tabMode: 'shift',
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
        if (event.keyCode === 13 && event.shiftKey) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        } else {
            return false;
        };
    };

    CodeCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.focus();
    };


    CodeCell.prototype.append_pyout = function (data, n) {
        var toinsert = $("<div/>").addClass("output_area output_pyout hbox");
        toinsert.append($('<div/>').
            addClass('prompt output_prompt').
            html('Out[' + n + ']:')
        );
        this.append_display_data(data, toinsert);
        toinsert.children().last().addClass("box_flex1");
        this.element.find("div.output").append(toinsert);
        // If we just output latex, typeset it.
        if (data["text/latex"] !== undefined) {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        };
    };


    CodeCell.prototype.append_pyerr = function (ename, evalue, tb) {
        var s = '';
        var len = tb.length;
        for (var i=0; i<len; i++) {
            s = s + tb[i] + '\n';
        }
        s = s + '\n';
        this.append_stream(s);
    };


    CodeCell.prototype.append_display_data = function (data, element) {
        if (data["text/latex"] !== undefined) {
            this.append_latex(data["text/latex"], element);
            // If it is undefined, then we just appended to div.output, which
            // makes the latex visible and we can typeset it. The typesetting
            // has to be done after the latex is on the page.
            if (element === undefined) {
                MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
            };
        } else if (data["image/svg+xml"] !== undefined) {
            this.append_svg(data["image/svg+xml"], element);
        } else if (data["image/png"] !== undefined) {
            this.append_png(data["image/png"], element);
        } else if (data["text/plain"] !== undefined) {
            this.append_stream(data["text/plain"], element);
        };
        return element;
    };


    CodeCell.prototype.append_stream = function (data, element) {
        element = element || this.element.find("div.output");
        var toinsert = $("<div/>").addClass("output_area output_stream");
        toinsert.append($("<pre/>").html(utils.fixConsole(data)));
        element.append(toinsert);
        return element;
    };


    CodeCell.prototype.append_svg = function (svg, element) {
        element = element || this.element.find("div.output");
        var toinsert = $("<div/>").addClass("output_area output_svg");
        toinsert.append(svg);
        element.append(toinsert);
        return element;
    };


    CodeCell.prototype.append_png = function (png, element) {
        element = element || this.element.find("div.output");
        var toinsert = $("<div/>").addClass("output_area output_png");
        toinsert.append($("<img/>").attr('src','data:image/png;base64,'+png));
        element.append(toinsert);
        return element;
    };


    CodeCell.prototype.append_latex = function (latex, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        element = element || this.element.find("div.output");
        var toinsert = $("<div/>").addClass("output_area output_latex");
        toinsert.append(latex);
        element.append(toinsert);
        return element;
    }


    CodeCell.prototype.clear_output = function () {
        this.element.find("div.output").html("");
    };


    CodeCell.prototype.collapse = function () {
        this.element.find('div.output').hide();
    };


    CodeCell.prototype.expand = function () {
        this.element.find('div.output').show();
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
        if (data.cell_type === 'code') {
            this.set_code(data.code);
            this.set_input_prompt(data.prompt_number);
        };
    };


    CodeCell.prototype.toJSON = function () {
        return {
            code : this.get_code(),
            cell_type : 'code',
            prompt_number : this.input_prompt_number
        };
    };

    IPython.CodeCell = CodeCell;

    return IPython;
}(IPython));

