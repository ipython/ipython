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

    var Cell = function (notebook) {
        this.notebook = notebook;
        this.read_only = false;
        if (notebook){
            this.read_only = notebook.read_only;
        }
        this.selected = false;
        this.element = null;
        this.create_element();
        if (this.element !== null) {
            this.set_autoindent(true);
            this.element.data("cell", this);
            this.bind_events();
        }
        this.cell_id = utils.uuid();
    };


    Cell.prototype.select = function () {
        this.element.addClass('ui-widget-content ui-corner-all');
        this.selected = true;
    };


    Cell.prototype.unselect = function () {
        this.element.removeClass('ui-widget-content ui-corner-all');
        this.selected = false;
    };


    Cell.prototype.bind_events = function () {
        var that = this;
        var nb = that.notebook;
        that.element.click(function (event) {
            if (that.selected === false) {
                nb.select(nb.find_cell_index(that));
            }
        });
        that.element.focusin(function (event) {
            if (that.selected === false) {
                nb.select(nb.find_cell_index(that));
            }
        });
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


    Cell.prototype.set_autoindent = function (state) {
        if (state) {
            this.code_mirror.setOption('tabMode', 'indent');
            this.code_mirror.setOption('enterMode', 'indent');
        } else {
            this.code_mirror.setOption('tabMode', 'shift');
            this.code_mirror.setOption('enterMode', 'flat');
        }
    };

    // Subclasses must implement create_element.
    Cell.prototype.create_element = function () {};

    // typeset with MathJax if MathJax is available
    Cell.prototype.typeset = function () {
        if (window.MathJax){
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        }
    };

    IPython.Cell = Cell;

    return IPython;

}(IPython));

