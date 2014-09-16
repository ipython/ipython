// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'base/js/utils',
    'jquery',
    'notebook/js/cell',
    'base/js/security',
    'notebook/js/mathjaxutils',
    'notebook/js/celltoolbar',
    'components/marked/lib/marked',
], function(IPython, utils, $, cell, security, mathjaxutils, celltoolbar, marked) {
    "use strict";
    var Cell = cell.Cell;

    var TextCell = function (options) {
        // Constructor
        //
        // Construct a new TextCell, codemirror mode is by default 'htmlmixed', 
        // and cell type is 'text' cell start as not redered.
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance 
        //          config: dictionary
        //          keyboard_manager: KeyboardManager instance 
        //          notebook: Notebook instance
        options = options || {};

        // in all TextCell/Cell subclasses
        // do not assign most of members here, just pass it down
        // in the options dict potentially overwriting what you wish.
        // they will be assigned in the base class.
        this.notebook = options.notebook;
        this.events = options.events;
        this.config = options.config;
        
        // we cannot put this as a class key as it has handle to "this".
        var cm_overwrite_options  = {
            onKeyEvent: $.proxy(this.handle_keyevent,this)
        };
        var config = utils.mergeopt(TextCell, this.config, {cm_config:cm_overwrite_options});
        Cell.apply(this, [{
                    config: config, 
                    keyboard_manager: options.keyboard_manager, 
                    events: this.events}]);

        this.cell_type = this.cell_type || 'text';
        mathjaxutils = mathjaxutils;
        this.rendered = false;
    };

    TextCell.prototype = new Cell();

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
        Cell.prototype.create_element.apply(this, arguments);

        var cell = $("<div>").addClass('cell text_cell');
        cell.attr('tabindex','2');

        var prompt = $('<div/>').addClass('prompt input_prompt');
        cell.append(prompt);
        var inner_cell = $('<div/>').addClass('inner_cell');
        this.celltoolbar = new celltoolbar.CellToolbar({
            cell: this, 
            notebook: this.notebook});
        inner_cell.append(this.celltoolbar.element);
        var input_area = $('<div/>').addClass('input_area');
        this.code_mirror = new CodeMirror(input_area.get(0), this.cm_config);
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('text_cell_render rendered_html')
            .attr('tabindex','-1');
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
        Cell.prototype.bind_events.apply(this);
        var that = this;

        this.element.dblclick(function () {
            if (that.selected === false) {
                this.events.trigger('select.Cell', {'cell':that});
            }
            var cont = that.unrender();
            if (cont) {
                that.focus_editor();
            }
        });
    };

    // Cell level actions
    
    TextCell.prototype.select = function () {
        var cont = Cell.prototype.select.apply(this);
        if (cont) {
            if (this.mode === 'edit') {
                this.code_mirror.refresh();
            }
        }
        return cont;
    };

    TextCell.prototype.unrender = function () {
        if (this.read_only) return;
        var cont = Cell.prototype.unrender.apply(this);
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
        this.unrender();
        this.code_mirror.refresh();
    };

    /**
     * setter :{{#crossLink "TextCell/set_rendered"}}{{/crossLink}}
     * @method get_rendered
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
        Cell.prototype.fromJSON.apply(this, arguments);
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
        var data = Cell.prototype.toJSON.apply(this);
        data.source = this.get_text();
        if (data.source == this.placeholder) {
            data.source = "";
        }
        return data;
    };


    var MarkdownCell = function (options) {
        // Constructor
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance 
        //          config: dictionary
        //          keyboard_manager: KeyboardManager instance 
        //          notebook: Notebook instance
        options = options || {};
        var config = utils.mergeopt(MarkdownCell, options.config);
        TextCell.apply(this, [$.extend({}, options, {config: config})]);

        this.cell_type = 'markdown';
    };

    MarkdownCell.options_default = {
        cm_config: {
            mode: 'ipythongfm'
        },
        placeholder: "Type *Markdown* and LaTeX: $\\alpha^2$"
    };

    MarkdownCell.prototype = new TextCell();

    /**
     * @method render
     */
    MarkdownCell.prototype.render = function () {
        var cont = TextCell.prototype.render.apply(this);
        if (cont) {
            var text = this.get_text();
            var math = null;
            if (text === "") { text = this.placeholder; }
            var text_and_math = mathjaxutils.remove_math(text);
            text = text_and_math[0];
            math = text_and_math[1];
            var html = marked.parser(marked.lexer(text));
            html = mathjaxutils.replace_math(html, math);
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


    var RawCell = function (options) {
        // Constructor
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance 
        //          config: dictionary
        //          keyboard_manager: KeyboardManager instance 
        //          notebook: Notebook instance
        options = options || {};
        var config = utils.mergeopt(RawCell, options.config);
        TextCell.apply(this, [$.extend({}, options, {config: config})]);

        // RawCell should always hide its rendered div
        this.element.find('div.text_cell_render').hide();
        this.cell_type = 'raw';
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
        this._auto_highlight(this.config.raw_cell_highlight);
    };

    /** @method render **/
    RawCell.prototype.render = function () {
        var cont = TextCell.prototype.render.apply(this);
        if (cont){
            var text = this.get_text();
            if (text === "") { text = this.placeholder; }
            this.set_text(text);
            this.element.removeClass('rendered');
        }
        return cont;
    };


    var HeadingCell = function (options) {
        // Constructor
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance 
        //          config: dictionary
        //          keyboard_manager: KeyboardManager instance 
        //          notebook: Notebook instance
        options = options || {};
        var config = utils.mergeopt(HeadingCell, options.config);
        TextCell.apply(this, [$.extend({}, options, {config: config})]);

        this.level = 1;
        this.cell_type = 'heading';
    };

    HeadingCell.options_default = {
        cm_config: {
            theme: 'heading-1'
        },
        placeholder: "Type Heading Here"
    };

    HeadingCell.prototype = new TextCell();

    /** @method fromJSON */
    HeadingCell.prototype.fromJSON = function (data) {
        if (data.level !== undefined){
            this.level = data.level;
        }
        TextCell.prototype.fromJSON.apply(this, arguments);
        this.code_mirror.setOption("theme", "heading-"+this.level);
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
        this.code_mirror.setOption("theme", "heading-"+level);

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


    HeadingCell.prototype.get_rendered = function () {
        var r = this.element.find("div.text_cell_render");
        return r.children().first().html();
    };

    HeadingCell.prototype.render = function () {
        var cont = TextCell.prototype.render.apply(this);
        if (cont) {
            var text = this.get_text();
            var math = null;
            // Markdown headings must be a single line
            text = text.replace(/\n/g, ' ');
            if (text === "") { text = this.placeholder; }
            text = new Array(this.level + 1).join("#") + " " + text;
            var text_and_math = mathjaxutils.remove_math(text);
            text = text_and_math[0];
            math = text_and_math[1];
            var html = marked.parser(marked.lexer(text));
            html = mathjaxutils.replace_math(html, math);
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

    // Backwards compatability.
    IPython.TextCell = TextCell;
    IPython.MarkdownCell = MarkdownCell;
    IPython.RawCell = RawCell;
    IPython.HeadingCell = HeadingCell;

    var textcell = {
        'TextCell': TextCell,
        'MarkdownCell': MarkdownCell,
        'RawCell': RawCell,
        'HeadingCell': HeadingCell,
    };
    return textcell;
});
