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
        this.placeholder = this.placeholder || '\u0000';
        IPython.Cell.apply(this, arguments);
        this.rendered = false;
        this.cell_type = this.cell_type || 'text';
    };


    TextCell.prototype = new IPython.Cell();


    TextCell.prototype.create_element = function () {
        var cell = $("<div>").addClass('cell text_cell border-box-sizing');
        cell.attr('tabindex','2');
        var input_area = $('<div/>').addClass('text_cell_input');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            mode: this.code_mirror_mode,
            theme: 'default',
            value: this.placeholder,
            readOnly: this.read_only
        });
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render').
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
                    event.preventDefault();
                }
            }
        });
    };


    TextCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.text_cell_render");
        output.trigger('focus');
    };


    TextCell.prototype.edit = function () {
        if ( this.read_only ) return;
        if (this.rendered === true) {
            var text_cell = this.element;
            var output = text_cell.find("div.text_cell_render");  
            output.hide();
            text_cell.find('div.text_cell_input').show();
            this.code_mirror.focus();
            this.code_mirror.refresh();
            this.rendered = false;
            if (this.get_source() === this.placeholder) {
                this.set_source('');
            }
        }
    };


    // Subclasses must define render.
    TextCell.prototype.render = function () {};


    TextCell.prototype.config_mathjax = function () {
        var text_cell = this.element;
        var that = this;
        text_cell.click(function () {
            that.edit();
        }).focusout(function () {
            that.render();
        });
        
        text_cell.trigger("focusout");
    };


    TextCell.prototype.get_source = function() {
        return this.code_mirror.getValue();
    };


    TextCell.prototype.set_source = function(text) {
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
                this.set_source(data.source);
                this.set_rendered(data.rendered || '');
                this.rendered = false;
                this.render();
            }
        }
    };


    TextCell.prototype.toJSON = function () {
        var data = {};
        data.cell_type = this.cell_type;
        data.source = this.get_source();
        return data;
    };


    // HTMLCell

    var HTMLCell = function (notebook) {
        this.placeholder = "\u0000Type <strong>HTML</strong> and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'html';
    };


    HTMLCell.prototype = new TextCell();


    HTMLCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_source();
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
        this.placeholder = "\u0000Type *Markdown* and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'markdown';
    };


    MarkdownCell.prototype = new TextCell();


    MarkdownCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_source();
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
        this.placeholder = "\u0000Type *ReStructured Text* and LaTeX: $\\alpha^2$";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'rst';
    };


    RSTCell.prototype = new TextCell();


    RSTCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_source();
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

