
//============================================================================
// RSTCell
//============================================================================

var IPython = (function (IPython) {

    var RSTCell = function (notebook) {
        IPython.Cell.apply(this, arguments);
        this.placeholder = "Type ReStructured Text *here*."
        this.rendered = false;
    };


    RSTCell.prototype = new IPython.Cell();



    RSTCell.prototype.create_element = function () {
        var cell = $("<div>").addClass('cell rst_cell border-box-sizing');
        var input_area = $('<div/>').addClass('rst_cell_input');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            enterMode : 'flat',
            tabMode: 'shift',
            mode: 'rst',
            theme: 'default',
            value: this.placeholder
        });
        // The tabindex=-1 makes this div focusable.
        var render_area = $('<div/>').addClass('rst_cell_render').
            addClass('rendered_html').attr('tabindex','-1');
        cell.append(input_area).append(render_area);
        this.element = cell;
    };


    RSTCell.prototype.bind_events = function () {
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


    RSTCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        var output = this.element.find("div.rst_cell_render");
        output.trigger('focus');
    };


    RSTCell.prototype.edit = function () {
        if (this.rendered === true) {
            var rst_cell = this.element;
            var output = rst_cell.find("div.rst_cell_render");  
            output.hide();
            rst_cell.find('div.rst_cell_input').show();
            this.code_mirror.focus();
            this.code_mirror.refresh();
            this.rendered = false;
        };
    };


    RSTCell.prototype.render = function () {
        if (this.rendered === false) {
            var text = this.get_source();
            if (text === '') {text = this.placeholder;};
            var html = IPython.markdown_converter.makeHtml(text);
            this.set_rendered(html);
            MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
            this.element.find('div.rst_cell_input').hide();
            this.element.find("div.rst_cell_render").show();
            this.rendered = true;
        };
    };


    RSTCell.prototype.render_rst = function () {
        if (this.rendered === false) {  
            var text = this.get_source();
            if (text === "") {text = this.placeholder;};
            var settings = {
                processData : false,
                cache : false,
                type : "POST",
                data : text,
                headers : {'Content-Type': 'application/x-rst'},
                success : $.proxy(this.handle_rendered,this)
            };
            $.ajax("/rstservice/render", settings);
        };
    };


    RSTCell.prototype.handle_rendered = function (data, status, xhr) {
        this.set_rendered(data);
        MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        this.element.find('div.rst_cell_input').hide();
        this.element.find("div.rst_cell_render").show();
        this.rendered = true;
    };


    RSTCell.prototype.config_mathjax = function () {
        var rst_cell = this.element;
        var that = this;
        rst_cell.click(function () {
            that.edit();
        }).focusout(function () {
            that.render();
        });
        
        rst_cell.trigger("focusout");
    };


    RSTCell.prototype.get_source = function () {
        return this.code_mirror.getValue();
    };


    RSTCell.prototype.set_source = function (text) {
        this.code_mirror.setValue(text);
        this.code_mirror.refresh();
    };


    RSTCell.prototype.set_rendered = function (text) {
        this.element.find('div.rst_cell_render').html(text);
    };


    RSTCell.prototype.get_rendered = function () {
        return this.element.find('div.rst_cell_render').html();
    };


    RSTCell.prototype.at_top = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    RSTCell.prototype.at_bottom = function () {
        if (this.rendered) {
            return true;
        } else {
            return false;
        }
    };


    RSTCell.prototype.fromJSON = function (data) {
        if (data.cell_type === 'rst') {
            if (data.source !== undefined) {
                this.set_source(data.source);
                this.set_rendered(data.rendered);
            };
        };
    }


    RSTCell.prototype.toJSON = function () {
        var data = {}
        data.cell_type = 'rst';
        data.source = this.get_source();
        data.rendered = this.get_rendered();
        return data;
    };

    IPython.RSTCell = RSTCell;

    return IPython;

}(IPython));

