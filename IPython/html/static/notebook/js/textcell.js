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
    "use strict";

    // TextCell base class
    var keycodes = IPython.keyboard.keycodes;
    var security = IPython.security;

    /**
     * Construct a new TextCell, codemirror mode is by default 'htmlmixed', and cell type is 'text'
     * cell start as not redered.
     *
     * @class TextCell
     * @constructor TextCell
     * @extend IPython.Cell
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
            onKeyEvent: $.proxy(this.handle_keyevent,this)
        };

        options = this.mergeopt(TextCell,options,{cm_config:cm_overwrite_options});

        this.cell_type = this.cell_type || 'text';

        IPython.Cell.apply(this, [options]);

        this.rendered = false;
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

        var prompt = $('<div/>').addClass('prompt input_prompt');
        cell.append(prompt);
        var inner_cell = $('<div/>').addClass('inner_cell');
        this.celltoolbar = new IPython.CellToolbar(this);
        inner_cell.append(this.celltoolbar.element);
        var input_area = $('<div/>').addClass('input_area');
        this.code_mirror = new CodeMirror(input_area.get(0), this.cm_config);
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render border-box-sizing').
            addClass('rendered_html').attr('tabindex','-1');
        inner_cell.append(input_area).append(render_area);
        cell.append(inner_cell);
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

        this.element.dblclick(function () {
            if (that.selected === false) {
                $([IPython.events]).trigger('select.Cell', {'cell':that});
            }
            var cont = that.unrender();
            if (cont) {
                that.focus_editor();
            }
        });
    };

    // Cell level actions
    
    TextCell.prototype.select = function () {
        var cont = IPython.Cell.prototype.select.apply(this);
        if (cont) {
            if (this.mode === 'edit') {
                this.code_mirror.refresh();
            }
        }
        return cont;
    };

    TextCell.prototype.unrender = function () {
        if (this.read_only) return;
        var cont = IPython.Cell.prototype.unrender.apply(this);
        if (cont) {
            var text_cell = this.element;
            var output = text_cell.find("div.text_cell_render");
            output.hide();
            text_cell.find('div.input_area').show();
            if (this.get_text() === this.placeholder) {
                this.set_text('');
            }
            this.refresh();
        }
        return cont;
    };

    TextCell.prototype.execute = function () {
        this.render();
    };

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
                // TODO: This HTML needs to be treated as potentially dangerous
                // user input and should be handled before set_rendered.         
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
        data.source = this.get_text();
        if (data.source == this.placeholder) {
            data.source = "";
        }
        return data;
    };


    /**
     * @class MarkdownCell
     * @constructor MarkdownCell
     * @extends IPython.HTMLCell
     */
    var MarkdownCell = function (options) {
        options = this.mergeopt(MarkdownCell, options);

        this.cell_type = 'markdown';
        TextCell.apply(this, [options]);
    };

    MarkdownCell.options_default = {
        cm_config: {
            mode: 'gfm'
        },
        placeholder: "Type *Markdown* and LaTeX: $\\alpha^2$"
    };

    MarkdownCell.prototype = new TextCell();

    /**
     * @method render
     */
    MarkdownCell.prototype.render = function () {
        var cont = IPython.TextCell.prototype.render.apply(this);
        if (cont) {
            var text = this.get_text();
            var math = null;
            if (text === "") { text = this.placeholder; }
            var text_and_math = IPython.mathjaxutils.remove_math(text);
            text = text_and_math[0];
            math = text_and_math[1];
            var html = marked.parser(marked.lexer(text));
            html = IPython.mathjaxutils.replace_math(html, math);
            html = security.sanitize_html(html);
            html = $($.parseHTML(html));
            // links in markdown cells should open in new tabs
            html.find("a[href]").not('[href^="#"]').attr("target", "_blank");
            this.set_rendered(html);
            this.element.find('div.input_area').hide();
            this.element.find("div.text_cell_render").show();
            this.typeset();
        }
        return cont;
    };


    // RawCell

    /**
     * @class RawCell
     * @constructor RawCell
     * @extends IPython.TextCell
     */
    var RawCell = function (options) {

        options = this.mergeopt(RawCell,options);
        TextCell.apply(this, [options]);
        this.cell_type = 'raw';
        // RawCell should always hide its rendered div
        this.element.find('div.text_cell_render').hide();
    };

    RawCell.options_default = {
        placeholder : "Write raw LaTeX or other formats here, for use with nbconvert. " +
            "It will not be rendered in the notebook. " + 
            "When passing through nbconvert, a Raw Cell's content is added to the output unmodified."
    };

    RawCell.prototype = new TextCell();

    /** @method bind_events **/
    RawCell.prototype.bind_events = function () {
        TextCell.prototype.bind_events.apply(this);
        var that = this;
        this.element.focusout(function() {
            that.auto_highlight();
            that.render();
        });

        this.code_mirror.on('focus', function() { that.unrender(); });
    };

    /**
     * Trigger autodetection of highlight scheme for current cell
     * @method auto_highlight
     */
    RawCell.prototype.auto_highlight = function () {
        this._auto_highlight(IPython.config.raw_cell_highlight);
    };

    /** @method render **/
    RawCell.prototype.render = function () {
        var cont = IPython.TextCell.prototype.render.apply(this);
        if (cont){
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_text(text);
            this.element.removeClass('rendered');
        }
        return cont;
    };


    /**
     * @class HeadingCell
     * @extends IPython.TextCell
     */

    /**
     * @constructor HeadingCell
     * @extends IPython.TextCell
     */
    var HeadingCell = function (options) {
        options = this.mergeopt(HeadingCell, options);

        this.level = 1;
        this.cell_type = 'heading';
        TextCell.apply(this, [options]);

        /**
         * heading level of the cell, use getter and setter to access
         * @property level
         */
    };

    HeadingCell.options_default = {
        placeholder: "Type Heading Here"
    };

    HeadingCell.prototype = new TextCell();

    /** @method fromJSON */
    HeadingCell.prototype.fromJSON = function (data) {
        if (data.level !== undefined){
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
     * can the cell be split into two cells
     * @method is_splittable
     **/
    HeadingCell.prototype.is_splittable = function () {
        return false;
    };


    /**
     * can the cell be merged with other cells
     * @method is_mergeable
     **/
    HeadingCell.prototype.is_mergeable = function () {
        return false;
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
        }
    };

    /** The depth of header cell, based on html (h1 to h6)
     * @method get_level
     * @return {integer} level - for 1 to 6
     */
    HeadingCell.prototype.get_level = function () {
        return this.level;
    };


    HeadingCell.prototype.set_rendered = function (html) {
        this.element.find("div.text_cell_render").html(html);
    };


    HeadingCell.prototype.get_rendered = function () {
        var r = this.element.find("div.text_cell_render");
        return r.children().first().html();
    };


    HeadingCell.prototype.render = function () {
        var cont = IPython.TextCell.prototype.render.apply(this);
        if (cont) {
            var text = this.get_text();
            var math = null;
            // Markdown headings must be a single line
            text = text.replace(/\n/g, ' ');
            if (text === "") { text = this.placeholder; }
            text = Array(this.level + 1).join("#") + " " + text;
            var text_and_math = IPython.mathjaxutils.remove_math(text);
            text = text_and_math[0];
            math = text_and_math[1];
            var html = marked.parser(marked.lexer(text));
            html = IPython.mathjaxutils.replace_math(html, math);
            html = security.sanitize_html(html);
            var h = $($.parseHTML(html));
            // add id and linkback anchor
            var hash = h.text().trim().replace(/ /g, '-');
            h.attr('id', hash);
            h.append(
                $('<a/>')
                    .addClass('anchor-link')
                    .attr('href', '#' + hash)
                    .text('¶')
            );
            this.set_rendered(h);
            this.element.find('div.input_area').hide();
            this.element.find("div.text_cell_render").show();
            this.typeset();
        }
        return cont;
    };

    IPython.TextCell = TextCell;
    IPython.MarkdownCell = MarkdownCell;
    IPython.RawCell = RawCell;
    IPython.HeadingCell = HeadingCell;


    return IPython;

}(IPython));

