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

    var TextCell = function () {
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
            lineWrapping : true,
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
            if (event.which === 13 && !event.shiftKey) {
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
            this.code_mirror.refresh();
            this.code_mirror.focus();
            // We used to need an additional refresh() after the focus, but
            // it appears that this has been fixed in CM. This bug would show
            // up on FF when a newly loaded markdown cell was edited.
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
        IPython.Cell.prototype.fromJSON.apply(this, arguments);
        if (data.cell_type === this.cell_type) {
            if (data.source !== undefined) {
                this.set_text(data.source);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                this.code_mirror.clearHistory();
                this.set_rendered(data.rendered || '');
                this.rendered = false;
                this.render();
            }
        }
    };


    TextCell.prototype.toJSON = function () {
        var data = IPython.Cell.prototype.toJSON.apply(this);
        data.cell_type = this.cell_type;
        data.source = this.get_text();
        return data;
    };


    // HTMLCell

    var HTMLCell = function () {
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

    var MarkdownCell = function () {
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
            try {
                this.set_rendered(html);
            } catch (e) {
                console.log("Error running Javascript in Markdown:");
                console.log(e);
                this.set_rendered($("<div/>").addClass("js-error").html(
                    "Error rendering Markdown!<br/>" + e.toString())
                );
            }
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


    // RawCell

    var RawCell = function () {
        this.placeholder = "Type plain text and LaTeX: $\\alpha^2$";
        this.code_mirror_mode = 'rst';
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'raw';
    };


    RawCell.prototype = new TextCell();


    RawCell.prototype.render = function () {
        this.rendered = true;
        this.edit();
    };


    RawCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.refresh();
        this.code_mirror.focus();
    };


    RawCell.prototype.at_top = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === 0) {
            return true;
        } else {
            return false;
        }
    };


    RawCell.prototype.at_bottom = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === (this.code_mirror.lineCount()-1)) {
            return true;
        } else {
            return false;
        }
    };


    // HTMLCell

    var HeadingCell = function () {
        this.placeholder = "Type Heading Here";
        IPython.TextCell.apply(this, arguments);
        this.cell_type = 'heading';
        this.level = 1;
    };


    HeadingCell.prototype = new TextCell();


    HeadingCell.prototype.fromJSON = function (data) {
        if (data.level != undefined){
            this.level = data.level;
        }
        IPython.TextCell.prototype.fromJSON.apply(this, arguments);
    };


    HeadingCell.prototype.toJSON = function () {
        var data = IPython.TextCell.prototype.toJSON.apply(this);
        data.level = this.get_level();
        return data;
    };


    HeadingCell.prototype.set_level = function (level) {
        this.level = level;
        if (this.rendered) {
            this.rendered = false;
            this.render();
        };
    };


    HeadingCell.prototype.get_level = function () {
        return this.level;
    };


    HeadingCell.prototype.set_rendered = function (text) {
        var r = this.element.find("div.text_cell_render");
        r.empty();
        r.append($('<h'+this.level+'/>').html(text));
    };


    HeadingCell.prototype.get_rendered = function () {
        var r = this.element.find("div.text_cell_render");
        return r.children().first().html();
    };


    HeadingCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_rendered(text);
            this.typeset();
            this.element.find('div.text_cell_input').hide();
            this.element.find("div.text_cell_render").show();
            this.rendered = true;
        };
    };

    IPython.TextCell = TextCell;
    IPython.HTMLCell = HTMLCell;
    IPython.MarkdownCell = MarkdownCell;
    IPython.RawCell = RawCell;
    IPython.HeadingCell = HeadingCell;


    return IPython;

}(IPython));

