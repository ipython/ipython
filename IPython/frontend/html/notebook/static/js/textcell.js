
//============================================================================
// TextCell
//============================================================================


var TextCell = function (notebook) {
    Cell.apply(this, arguments);
    this.placeholder = "Type <strong>HTML</strong> and LaTeX: $\\alpha^2$"
    this.rendered = false;
};


TextCell.prototype = new Cell();


TextCell.prototype.create_element = function () {
    var cell = $("<div>").addClass('cell text_cell').
               append(
                   $("<textarea>" + this.placeholder + "</textarea>").
                   addClass('text_cell_input monospace-font').
                   attr('rows',1).
                   attr('cols',80).
                   autogrow()
               ).append(
                   // The tabindex=-1 makes this div focusable.
                   $('<div></div>').addClass('text_cell_render').attr('tabindex','-1')
               )
    this.element = cell;
};


TextCell.prototype.bind_events = function () {
    Cell.prototype.bind_events.apply(this);
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


TextCell.prototype.select = function () {
    Cell.prototype.select.apply(this);
    var output = this.element.find("div.text_cell_render");
    output.trigger('focus');
};


TextCell.prototype.edit = function () {
    if (this.rendered === true) {
        var text_cell = this.element;
        var input = text_cell.find("textarea.text_cell_input");
        var output = text_cell.find("div.text_cell_render");  
        output.hide();
        input.show().trigger('focus');
        this.rendered = false;
    };
};


TextCell.prototype.render = function () {
    if (this.rendered === false) {
        var text_cell = this.element;
        var input = text_cell.find("textarea.text_cell_input");
        var output = text_cell.find("div.text_cell_render");    
        var text = input.val();
        if (text === "") {
            text = this.placeholder;
            input.val(text);
        };
        output.html(text)
        input.html(text);
        MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
        input.hide();
        output.show();
        this.rendered = true;
    };
};


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


TextCell.prototype.get_text = function() {
    return this.element.find("textarea.text_cell_input").val();
};


TextCell.prototype.set_text = function(text) {
    this.element.find("textarea.text_cell_input").val(text);
    this.element.find("textarea.text_cell_input").html(text);
    this.element.find("div.text_cell_render").html(text);
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
    if (data.cell_type === 'text') {
        this.set_text(data.text);
        this.grow(this.element.find("textarea.text_cell_input"));
    };
}


TextCell.prototype.toJSON = function () {
    return {
        cell_type : 'text',
        text : this.get_text(),
    };
};


