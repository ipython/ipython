//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;


    var Cell = function () {
        this.placeholder = this.placeholder || '';
        this.read_only = false;
        this.selected = false;
        this.element = null;
        this.metadata = {};
        this.create_element();
        if (this.element !== null) {
            this.element.data("cell", this);
            this.bind_events();
        }
        this.cell_id = utils.uuid();
    };


    // Subclasses must implement create_element.
    Cell.prototype.create_element = function () {};


    Cell.prototype.bind_events = function () {
        var that = this;
        // We trigger events so that Cell doesn't have to depend on Notebook.
        that.element.click(function (event) {
            if (that.selected === false) {
                $([IPython.events]).trigger('select.Cell', {'cell':that});
            }
        });
        that.element.focusin(function (event) {
            if (that.selected === false) {
                $([IPython.events]).trigger('select.Cell', {'cell':that});
            }
        });
    };


    // typeset with MathJax if MathJax is available
    Cell.prototype.typeset = function () {
        if (window.MathJax){
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    };


    Cell.prototype.select = function () {
        this.element.addClass('ui-widget-content ui-corner-all');
        this.selected = true;
    };


    Cell.prototype.unselect = function () {
        this.element.removeClass('ui-widget-content ui-corner-all');
        this.selected = false;
    };


    Cell.prototype.get_text = function () {
    };


    Cell.prototype.set_text = function (text) {
    };


    Cell.prototype.refresh = function () {
        this.code_mirror.refresh();
    };


    Cell.prototype.edit = function () {
    };


    Cell.prototype.render = function () {
    };


    Cell.prototype.toJSON = function () {
        var data = {};
        data.metadata = this.metadata;
        return data;
    };


    Cell.prototype.fromJSON = function (data) {
        if (data.metadata !== undefined) {
            this.metadata = data.metadata;
        }
    };


    Cell.prototype.is_splittable = function () {
        return true;
    };


    Cell.prototype.get_pre_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var text = this.code_mirror.getRange({line:0,ch:0}, cursor);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    }


    Cell.prototype.get_post_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var last_line_num = this.code_mirror.lineCount()-1;
        var last_line_len = this.code_mirror.getLine(last_line_num).length;
        var end = {line:last_line_num, ch:last_line_len}
        var text = this.code_mirror.getRange(cursor, end);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    };


    Cell.prototype.grow = function(element) {
        // Grow the cell by hand. This is used upon reloading from JSON, when the
        // autogrow handler is not called.
        var dom = element.get(0);
        var lines_count = 0;
        // modified split rule from
        // http://stackoverflow.com/questions/2035910/how-to-get-the-number-of-lines-in-a-textarea/2036424#2036424
        var lines = dom.value.split(/\r|\r\n|\n/);
        lines_count = lines.length;
        if (lines_count >= 1) {
            dom.rows = lines_count;
        } else {
            dom.rows = 1;
        }
    };


    Cell.prototype.toggle_line_numbers = function () {
        if (this.code_mirror.getOption('lineNumbers') == false) {
            this.code_mirror.setOption('lineNumbers', true);
        } else {
            this.code_mirror.setOption('lineNumbers', false);
        }
        this.code_mirror.refresh();
    };


    IPython.Cell = Cell;

    return IPython;

}(IPython));

