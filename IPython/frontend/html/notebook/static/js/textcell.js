//----------------------------------------------------------------------------
//  Copyright (C) 2008-2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// TextCell
//============================================================================



/**
    A module that allow to create different type of Text Cell
    @module IPython
    @namespace IPython
 */
var IPython = (function (IPython) {

    // TextCell base class
    var key = IPython.utils.keycodes;

    /**
     * Construct a new TextCell, codemirror mode is by default 'htmlmixed', and cell type is 'text'
     * cell start as not redered.
     *
     * @class TextCell
     * @constructor TextCell
     * @extend Ipython.Cell
     * @param {object|undefined} [options]
     *      @param [options.cm_config] {object} config to pass to CodeMirror, will extend/overwrite default config
     *      @param [options.placeholder] {string} default string to use when souce in empty for rendering (only use in some TextCell subclass)
     */
    var TextCell = function (options) {
        // in all TextCell/Cell subclasses
        // do not assign most of members here, just pass it down
        // in the options dict potentially overwriting what you wish.
        // they will be assigned in the base class.

        // we cannot put this as a class key as it has handle to "this".
        var cm_overwrite_options  = {
            onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        };

        options = this.mergeopt(TextCell,options,{cm_config:cm_overwrite_options});

        IPython.Cell.apply(this, [options]);


        this.rendered = false;
        this.cell_type = this.cell_type || 'text';
    };

    TextCell.prototype = new IPython.Cell();

    TextCell.options_default = {
        cm_config : {
            extraKeys: {"Tab": "indentMore","Shift-Tab" : "indentLess"},
            mode: 'htmlmixed',
            lineWrapping : true,
        }
    };



    /**
     * Create the DOM element of the TextCell
     * @method create_element
     * @private
     */
    TextCell.prototype.create_element = function () {
        IPython.Cell.prototype.create_element.apply(this, arguments);
        var cell = $("<div>").addClass('cell text_cell border-box-sizing');
        cell.attr('tabindex','2');

        this.celltoolbar = new IPython.CellToolbar(this);
        cell.append(this.celltoolbar.element);

        var input_area = $('<div/>').addClass('text_cell_input border-box-sizing');
        this.code_mirror = CodeMirror(input_area.get(0), this.cm_config);

        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render border-box-sizing').
            addClass('rendered_html').attr('tabindex','-1');
        cell.append(input_area).append(render_area);
        this.element = cell;
    };


    /**
     * Bind the DOM evet to cell actions
     * Need to be called after TextCell.create_element
     * @private
     * @method bind_event
     */
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

    /**
     * This method gets called in CodeMirror's onKeyDown/onKeyPress
     * handlers and is used to provide custom key handling.
     *
     * Subclass should override this method to have custom handeling
     *
     * @method handle_codemirror_keyevent
     * @param {CodeMirror} editor - The codemirror instance bound to the cell
     * @param {event} event -
     * @return {Boolean} `true` if CodeMirror should ignore the event, `false` Otherwise
     */
    TextCell.prototype.handle_codemirror_keyevent = function (editor, event) {

        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        }
        return false;
    };

    /**
     * Select the current cell and trigger 'focus'
     * @method select
     */
    TextCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.text_cell_render");
        output.trigger('focus');
    };

    /**
     * unselect the current cell and `render` it
     * @method unselect
     */
    TextCell.prototype.unselect = function() {
        // render on selection of another cell
        this.render();
        IPython.Cell.prototype.unselect.apply(this);
    };

    /**
     *
     * put the current cell in edition mode
     * @method edit
     */
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


    /**
     * Empty, Subclasses must define render.
     * @method render
     */
    TextCell.prototype.render = function () {};


    /**
     * setter: {{#crossLink "TextCell/set_text"}}{{/crossLink}}
     * @method get_text
     * @retrun {string} CodeMirror current text value
     */
    TextCell.prototype.get_text = function() {
        return this.code_mirror.getValue();
    };

    /**
     * @param {string} text - Codemiror text value
     * @see TextCell#get_text
     * @method set_text
     * */
    TextCell.prototype.set_text = function(text) {
        this.code_mirror.setValue(text);
        this.code_mirror.refresh();
    };

    /**
     * setter :{{#crossLink "TextCell/set_rendered"}}{{/crossLink}}
     * @method get_rendered
     * @return {html} html of rendered element
     * */
    TextCell.prototype.get_rendered = function() {
        return this.element.find('div.text_cell_render').html();
    };

    /**
     * @method set_rendered
     */
    TextCell.prototype.set_rendered = function(text) {
        this.element.find('div.text_cell_render').html(text);
    };

    /**
     * not deprecated, but implementation wrong
     * @method at_top
     * @deprecated
     * @return {Boolean} true is cell rendered, false otherwise
     * I doubt this is what it is supposed to do
     * this implementation is completly false
     */
    TextCell.prototype.at_top = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    /**
     * not deprecated, but implementation wrong
     * @method at_bottom
     * @deprecated
     * @return {Boolean} true is cell rendered, false otherwise
     * I doubt this is what it is supposed to do
     * this implementation is completly false
     * */
    TextCell.prototype.at_bottom = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };

    /**
     * Create Text cell from JSON
     * @param {json} data - JSON serialized text-cell
     * @method fromJSON
     */
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

    /** Generate JSON from cell
     * @return {object} cell data serialised to json
     */
    TextCell.prototype.toJSON = function () {
        var data = IPython.Cell.prototype.toJSON.apply(this);
        data.cell_type = this.cell_type;
        data.source = this.get_text();
        return data;
    };


    /**
     * @class MarkdownCell
     * @constructor MarkdownCell
     * @extends Ipython.HtmlCell
     */
    var MarkdownCell = function (options) {
        var options = options || {};

        options = this.mergeopt(MarkdownCell,options);
        TextCell.apply(this, [options]);

        this.cell_type = 'markdown';
    };

    MarkdownCell.options_default = {
        cm_config: {
            mode: 'markdown'
        },
        placeholder: "Type *Markdown* and LaTeX: $\\alpha^2$"
    }




    MarkdownCell.prototype = new TextCell();

    /**
     * @method render
     */
    MarkdownCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            text = IPython.mathjaxutils.remove_math(text);
            var html = marked.parser(marked.lexer(text));
            html = IPython.mathjaxutils.replace_math(html);
            try {
                this.set_rendered(html);
            } catch (e) {
                console.log("Error running Javascript in Markdown:");
                console.log(e);
                this.set_rendered($("<div/>").addClass("js-error").html(
                    "Error rendering Markdown!<br/>" + e.toString())
                );
            }
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
            this.typeset()
            this.rendered = true;
        }
    };


    // RawCell

    /**
     * @class RawCell
     * @constructor RawCell
     * @extends Ipython.TextCell
     */
    var RawCell = function (options) {

        options = this.mergeopt(RawCell,options)
        TextCell.apply(this, [options]);

        this.cell_type = 'raw';

        var that = this
        this.element.focusout(
                function() { that.auto_highlight(); }
            );
    };

    RawCell.options_default = {
        placeholder : "Type plain text and LaTeX: $\\alpha^2$"
    };



    RawCell.prototype = new TextCell();

    /**
     * Trigger autodetection of highlight scheme for current cell
     * @method auto_highlight
     */
    RawCell.prototype.auto_highlight = function () {
        this._auto_highlight(IPython.config.raw_cell_highlight);
    };

    /** @method render **/
    RawCell.prototype.render = function () {
        this.rendered = true;
        this.edit();
    };


    /** @method handle_codemirror_keyevent **/
    RawCell.prototype.handle_codemirror_keyevent = function (editor, event) {

        var that = this;
        if (event.which === key.UPARROW && event.type === 'keydown') {
            // If we are not at the top, let CM handle the up arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_top()) {
                event.stop();
                return false;
            } else {
                return true;
            };
        } else if (event.which === key.DOWNARROW && event.type === 'keydown') {
            // If we are not at the bottom, let CM handle the down arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_bottom()) {
                event.stop();
                return false;
            } else {
                return true;
            };
        };
        return false;
    };

    /** @method select **/
    RawCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.refresh();
        this.code_mirror.focus();
    };

    /** @method at_top **/
    RawCell.prototype.at_top = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === 0 && cursor.ch === 0) {
            return true;
        } else {
            return false;
        }
    };


    /** @method at_bottom **/
    RawCell.prototype.at_bottom = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === (this.code_mirror.lineCount()-1) && cursor.ch === this.code_mirror.getLine(cursor.line).length) {
            return true;
        } else {
            return false;
        }
    };


    /**
     * @class HeadingCell
     * @extends Ipython.TextCell
     */

    /**
     * @constructor HeadingCell
     * @extends Ipython.TextCell
     */
    var HeadingCell = function (options) {

        options = this.mergeopt(HeadingCell,options)
        TextCell.apply(this, [options]);

        /**
         * heading level of the cell, use getter and setter to access
         * @property level
         */
        this.level = 1;
        this.cell_type = 'heading';
    };

    HeadingCell.options_default = {
        placeholder: "Type Heading Here"
    };

    HeadingCell.prototype = new TextCell();

    /** @method fromJSON */
    HeadingCell.prototype.fromJSON = function (data) {
        if (data.level != undefined){
            this.level = data.level;
        }
        TextCell.prototype.fromJSON.apply(this, arguments);
    };


    /** @method toJSON */
    HeadingCell.prototype.toJSON = function () {
        var data = TextCell.prototype.toJSON.apply(this);
        data.level = this.get_level();
        return data;
    };


    /**
     * Change heading level of cell, and re-render
     * @method set_level
     */
    HeadingCell.prototype.set_level = function (level) {
        this.level = level;
        if (this.rendered) {
            this.rendered = false;
            this.render();
        };
    };

    /** The depth of header cell, based on html (h1 to h6)
     * @method get_level
     * @return {integer} level - for 1 to 6
     */
    HeadingCell.prototype.get_level = function () {
        return this.level;
    };


    HeadingCell.prototype.set_rendered = function (text) {
        var r = this.element.find("div.text_cell_render");
        r.empty();
        var link = text.replace(/ /g, '_');
        r.append(
            $('<h'+this.level+'/>')
            .append(
            $('<a/>')
                .addClass('heading-anchor')
                .attr('href', '#' + link)
                .attr('id', link)
                .html(text)
            )
        );
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
    IPython.MarkdownCell = MarkdownCell;
    IPython.RawCell = RawCell;
    IPython.HeadingCell = HeadingCell;


    return IPython;

}(IPython));

