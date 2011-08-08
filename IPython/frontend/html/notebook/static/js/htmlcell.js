
//============================================================================
// HTMLCell
//============================================================================

var IPython = (function (IPython) {

    var HTMLCell = function (notebook) {
        IPython.Cell.apply(this, arguments);
        this.placeholder = "Type <strong>HTML</strong> and LaTeX: $\\alpha^2$"
        this.rendered = false;
    };


    HTMLCell.prototype = new IPython.Cell();



    HTMLCell.prototype.create_element = function () {
        var cell = $("<div>").addClass('cell html_cell border-box-sizing');
        var input_area = $('<div/>').addClass('html_cell_input');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            enterMode : 'flat',
            tabMode: 'shift',
            value: this.placeholder
        });
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('html_cell_render').attr('tabindex','-1');
        cell.append(input_area).append(render_area);
        this.element = cell;
    };


    HTMLCell.prototype.bind_events = function () {
        IPython.Cell.prototype.bind_events.apply(this);
        var that = this;
        this.element.keydown(function (event) {
            if (event.which === 13) {
                if (that.rendered) {
                    that.edit();
                    event.preventDefault();
                };
            };
        });
    };


    HTMLCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.html_cell_render");
        output.trigger('focus');
    };


    HTMLCell.prototype.edit = function () {
        if (this.rendered === true) {
            var html_cell = this.element;
            var output = html_cell.find("div.html_cell_render");  
            output.hide();
            html_cell.find('div.html_cell_input').show();
            this.code_mirror.focus();
            this.code_mirror.refresh();
            this.rendered = false;
        };
    };


    HTMLCell.prototype.render = function () {
        if (this.rendered === false) {
            var html_cell = this.element;
            var output = html_cell.find("div.html_cell_render");    
            var text = this.get_source();
            if (text === "") {text = this.placeholder;};
            this.set_render(text);
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
            html_cell.find('div.html_cell_input').hide();
            output.show();
            this.rendered = true;
        };
    };


    HTMLCell.prototype.config_mathjax = function () {
        var html_cell = this.element;
        var that = this;
        html_cell.click(function () {
            that.edit();
        }).focusout(function () {
            that.render();
        });
        
        html_cell.trigger("focusout");
    };


    HTMLCell.prototype.get_source = function() {
        return this.code_mirror.getValue();
    };


    HTMLCell.prototype.set_source = function(text) {
        this.code_mirror.setValue(text);
        this.code_mirror.refresh();
    };


    HTMLCell.prototype.set_render = function(text) {
        this.element.find('div.html_cell_render').html(text);
    };


    HTMLCell.prototype.at_top = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    HTMLCell.prototype.at_bottom = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    HTMLCell.prototype.fromJSON = function (data) {
        if (data.cell_type === 'html') {
            if (data.source !== undefined) {
                this.set_source(data.source);
                this.set_render(data.source);
            };
        };
    }


    HTMLCell.prototype.toJSON = function () {
        var data = {}
        data.cell_type = 'html';
        data.source = this.get_source();
        return data;
    };

    IPython.HTMLCell = HTMLCell;

    return IPython;

}(IPython));

