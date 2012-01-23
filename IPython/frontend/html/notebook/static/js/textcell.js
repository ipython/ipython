//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// TextCell
//============================================================================

var IPython = (function (IPython) {

    // TextCell base class

    var TextCell = function (notebook) {
        this.code_mirror_mode = this.code_mirror_mode || 'htmlmixed';
        IPython.Cell.apply(this, arguments);
        this.rendered = false;
        this.cell_type = this.cell_type || 'text';
    };


    TextCell.prototype = new IPython.Cell();


    TextCell.prototype.create_element = function () {
        var cell = $("<div>").addClass('cell text_cell border-box-sizing');
        cell.attr('tabindex','2');
        var input_area = $('<div/>').addClass('text_cell_input border-box-sizing');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            mode: this.code_mirror_mode,
            theme: 'default',
            value: this.placeholder,
            readOnly: this.read_only,
            onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        });
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render border-box-sizing').
            addClass('rendered_html').attr('tabindex','-1');
        cell.append(input_area).append(render_area);
        this.element = cell;
    };


    TextCell.prototype.bind_events = function () {
        IPython.Cell.prototype.bind_events.apply(this);
        var that = this;
        this.element.keydown(function (event) {
            if (event.which === 13) {
                if (that.rendered) {
                    that.edit();
                    return false;
                };
            };
        });
        this.element.dblclick(function () {
            that.edit();
        });
    };


    TextCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress
        // handlers and is used to provide custom key handling. Its return
        // value is used to determine if CodeMirror should ignore the event:
        // true = ignore, false = don't ignore.

        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        }
        return false;
    };


    TextCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.text_cell_render");
        output.trigger('focus');
    };


    TextCell.prototype.unselect = function() {
        // render on selection of another cell
        this.render();
        IPython.Cell.prototype.unselect.apply(this);
    };


    TextCell.prototype.edit = function () {
        if ( this.read_only ) return;
        if (this.rendered === true) {
            var text_cell = this.element;
            var output = text_cell.find("div.text_cell_render");  
            output.hide();
            text_cell.find('div.text_cell_input').show();
            // I don't know why I need to do this, but if I don't do
            // refresh/focus/refresh, the to_markdown method won't work.
            this.code_mirror.refresh();
            this.code_mirror.focus();
            // This final refresh is needed on Firefox to trigger the editor
            // to be auto-sized. This glitch only happens on cell that are
            // loaded initially and haven't had their editor focused before.
            this.code_mirror.refresh();
            this.rendered = false;
            if (this.get_text() === this.placeholder) {
                this.set_text('');
                this.refresh();
            }
        }
    };


    // Subclasses must define render.
    TextCell.prototype.render = function () {};


    TextCell.prototype.get_text = function() {
        return this.code_mirror.getValue();
    };


    TextCell.prototype.set_text = function(text) {
        this.code_mirror.setValue(text);
        this.code_mirror.refresh();
    };


    TextCell.prototype.get_rendered = function() {
        return this.element.find('div.text_cell_render').html();
    };


    TextCell.prototype.set_rendered = function(text) {
        this.element.find('div.text_cell_render').html(text);
    };


    TextCell.prototype.at_top = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    TextCell.prototype.at_bottom = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    TextCell.prototype.fromJSON = function (data) {
        if (data.cell_type === this.cell_type) {
            if (data.source !== undefined) {
                this.set_text(data.source);
                this.set_rendered(data.rendered || '');
                this.rendered = false;
                this.render();
            }
        }
    };


    TextCell.prototype.toJSON = function () {
        var data = {};
        data.cell_type = this.cell_type;
        data.source = this.get_text();
        return data;
    };


    // HTMLCell

    var HTMLCell = function (notebook) {
        this.placeholder = "Type <strong>HTML</strong> and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'html';
    };


    HTMLCell.prototype = new TextCell();


    HTMLCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_rendered(text);
            this.typeset();
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            this.rendered = true;
        }
    };


    // MarkdownCell

    var MarkdownCell = function (notebook) {
        this.placeholder = "Type *Markdown* and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'markdown';
    };


    MarkdownCell.prototype = new TextCell();


    MarkdownCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            var html = IPython.markdown_converter.makeHtml(text);
            this.set_rendered(html);
            this.typeset()
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            var code_snippets = this.element.find("pre > code");
            code_snippets.replaceWith(function () {
                var code = $(this).html();
                /* Substitute br for newlines and &nbsp; for spaces
                   before highlighting, since prettify doesn't
                   preserve those on all browsers */
                code = code.replace(/(\r\n|\n|\r)/gm, "<br/>");
                code = code.replace(/ /gm, '&nbsp;');
                code = prettyPrintOne(code);

                return '<code class="prettyprint">' + code + '</code>';
            });
            this.rendered = true;
        }
    };


    // RSTCell

    var RSTCell = function (notebook) {
        this.placeholder = "Type *ReStructured Text* and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'rst';
    };


    RSTCell.prototype = new TextCell();


    RSTCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            var settings = {
                processData : false,
                cache : false,
                type : "POST",
                data : text,
                headers : {'Content-Type': 'application/x-rst'},
                success : $.proxy(this.handle_render,this)
            };
            $.ajax("/rstservice/render", settings);
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            this.set_rendered("Rendering...");
        }
    };


    RSTCell.prototype.handle_render = function (data, status, xhr) {
        this.set_rendered(data);
        this.typeset();
        this.rendered = true;
    };


    IPython.TextCell = TextCell;
    IPython.HTMLCell = HTMLCell;
    IPython.MarkdownCell = MarkdownCell;
    IPython.RSTCell = RSTCell;


    return IPython;

}(IPython));

