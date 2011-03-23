var IPYTHON = {};


//============================================================================
// Notebook
//============================================================================


var Notebook = function (selector) {
    this.element = $(selector);
    this.element.scroll();
    this.element.data("notebook", this);
    this.next_prompt_number = 1;
    this.bind_events();
};


Notebook.prototype.bind_events = function () {
    var that = this;
    $(document).keydown(function (event) {
        console.log(event);
        if (event.which == 38 && event.shiftKey) {
            event.preventDefault();
            that.select_prev();
        } else if (event.which == 40 && event.shiftKey) {
            event.preventDefault();
            that.select_next();
        } else if (event.which == 13 && event.shiftKey) {
            // The focus is not quite working here.
            event.preventDefault();
            that.insert_code_cell_after();
        }
    });
};


// Cell indexing, retrieval, etc.


Notebook.prototype.cell_elements = function () {
    return this.element.children("div.cell");
}


Notebook.prototype.ncells = function (cell) {
    return this.cell_elements().length;
}


// TODO: we are often calling cells as cells()[i], which we should optimize
// to cells(i) or a new method.
Notebook.prototype.cells = function () {
    return this.cell_elements().toArray().map(function (e) {
        return $(e).data("cell");
    });
}


Notebook.prototype.find_cell_index = function (cell) {
    var result = null;
    this.cell_elements().filter(function (index) {
        if ($(this).data("cell") === cell) {
            result = index;
        };
    });
    return result;
};


Notebook.prototype.index_or_selected = function (index) {
    return index || this.selected_index() || 0;
}


Notebook.prototype.select = function (index) {
    if (index !== undefined && index >= 0 && index < this.ncells()) {
        if (this.selected_index() !== null) {
            this.selected_cell().unselect();
        };
        this.cells()[index].select();
    };
    return this;
};


Notebook.prototype.select_next = function () {
    var index = this.selected_index();
    if (index !== null && index >= 0 && (index+1) < this.ncells()) {
        this.select(index+1);
    };
    return this;
};


Notebook.prototype.select_prev = function () {
    var index = this.selected_index();
    if (index !== null && index >= 0 && (index-1) < this.ncells()) {
        this.select(index-1);
    };
    return this;
};


Notebook.prototype.selected_index = function () {
    var result = null;
    this.cell_elements().filter(function (index) {
        if ($(this).data("cell").selected === true) {
            result = index;
        };
    });
    return result;
};


Notebook.prototype.selected_cell = function () {
    return this.cell_elements().eq(this.selected_index()).data("cell");
}


// Cell insertion, deletion and moving.


Notebook.prototype.delete_cell = function (index) {
    var i = index || this.selected_index();
    if (i !== null && i >= 0 && i < this.ncells()) {
        this.cell_elements().eq(i).remove();
        if (i === (this.ncells())) {
            this.select(i-1);
        } else {
            this.select(i);
        };
    };
    return this;
};


Notebook.prototype.append_cell = function (cell) {
    this.element.append(cell.element);
    return this;
};


Notebook.prototype.insert_cell_after = function (cell, index) {
    var ncells = this.ncells();
    if (ncells === 0) {
        this.append_cell(cell);
        return this;
    };
    if (index >= 0 && index < ncells) {
        this.cell_elements().eq(index).after(cell.element);
    };
    return this
};


Notebook.prototype.insert_cell_before = function (cell, index) {
    var ncells = this.ncells();
    if (ncells === 0) {
        this.append_cell(cell);
        return this;
    };
    if (index >= 0 && index < ncells) {
        this.cell_elements().eq(index).before(cell.element);
    };
    return this;
};


Notebook.prototype.move_cell_up = function (index) {
    var i = index || this.selected_index();
    if (i !== null && i < this.ncells() && i > 0) {
        var pivot = this.cell_elements().eq(i-1);
        var tomove = this.cell_elements().eq(i);
        if (pivot !== null && tomove !== null) {
            tomove.detach();
            pivot.before(tomove);
            this.select(i-1);
        };
    };
    return this;
}


Notebook.prototype.move_cell_down = function (index) {
    var i = index || this.selected_index();
    if (i !== null && i < (this.ncells()-1) && i >= 0) {
        var pivot = this.cell_elements().eq(i+1)
        var tomove = this.cell_elements().eq(i)
        if (pivot !== null && tomove !== null) {
            tomove.detach();
            pivot.after(tomove);
            this.select(i+1);
        };
    };
    return this;
}


Notebook.prototype.sort_cells = function () {
    var ncells = this.ncells();
    var sindex = this.selected_index();
    var swapped;
    do {
        swapped = false
        for (var i=1; i<ncells; i++) {
            current = this.cell_elements().eq(i).data("cell");
            previous = this.cell_elements().eq(i-1).data("cell");
            if (previous.input_prompt_number > current.input_prompt_number) {
                this.move_cell_up(i);
                swapped = true;
            };
        };
    } while (swapped);
    this.select(sindex);
    return this;
};


Notebook.prototype.insert_code_cell_before = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var cell = new CodeCell(this);
    cell.set_input_prompt(this.next_prompt_number);
    this.next_prompt_number = this.next_prompt_number + 1;
    this.insert_cell_before(cell, i);
    this.select(this.find_cell_index(cell));
    return this;
}


Notebook.prototype.insert_code_cell_after = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var cell = new CodeCell(this);
    cell.set_input_prompt(this.next_prompt_number);
    this.next_prompt_number = this.next_prompt_number + 1;
    this.insert_cell_after(cell, i);
    this.select(this.find_cell_index(cell));
    return this;
}


Notebook.prototype.insert_text_cell_before = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var cell = new TextCell(this);
    cell.config_mathjax();
    this.insert_cell_before(cell, i);
    this.select(this.find_cell_index(cell));
    return this;
}


Notebook.prototype.insert_text_cell_after = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var cell = new TextCell(this);
    cell.config_mathjax();
    this.insert_cell_after(cell, i);
    this.select(this.find_cell_index(cell));
    return this;
}


Notebook.prototype.text_to_code = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var source_element = this.cell_elements().eq(i);
    var source_cell = source_element.data("cell");
    if (source_cell instanceof TextCell) {
        this.insert_code_cell_after(i);
        var target_cell = this.cells()[i+1];
        var text = source_element.find("textarea.text_cell_input").val();
        target_cell.element.find("textarea.input_area").val(text);
        source_element.remove();
    };
};


Notebook.prototype.code_to_text = function (index) {
    // TODO: Bounds check for i
    var i = this.index_or_selected(index);
    var source_element = this.cell_elements().eq(i);
    var source_cell = source_element.data("cell");
    if (source_cell instanceof CodeCell) {
        this.insert_text_cell_after(i);
        var target_cell = this.cells()[i+1];
        var text = source_element.find("textarea.input_area").val();
        if (text === "") {text = target_cell.placeholder;};
        target_cell.element.find("textarea.text_cell_input").val(text);
        target_cell.element.find("textarea.text_cell_input").html(text);
        target_cell.element.find("div.text_cell_render").html(text);

        source_element.remove();
    };
};


// Cell collapsing

Notebook.prototype.collapse = function (index) {
    var i = this.index_or_selected(index);
    this.cells()[i].collapse();
}


Notebook.prototype.expand = function (index) {
    var i = this.index_or_selected(index);
    this.cells()[i].expand();
}


//============================================================================
// Cell
//============================================================================


var Cell = function (notebook) {
    this.notebook = notebook;
    this.selected = false;
    this.element;
    this.create_element();
    if (this.element !== undefined) {
        this.element.data("cell", this);
        this.bind_events();
    }
};


Cell.prototype.select = function () {
    this.element.addClass('ui-widget-content ui-corner-all');
    this.selected = true;
    // TODO: we need t test across browsers to see if both of these are needed.
    // In the meantime, there should not be any harm in having them both.
    this.element.find('textarea').trigger('focusin');
    this.element.find('textarea').trigger('focus');
};


Cell.prototype.unselect = function () {
    this.element.removeClass('ui-widget-content ui-corner-all');
    this.selected = false;
};


Cell.prototype.bind_events = function () {
    var that = this;
    var nb = that.notebook
    that.element.click(function (event) {
        if (that.selected === false) {
            nb.select(nb.find_cell_index(that));
        };
    });
    that.element.focusin(function (event) {
        if (that.selected === false) {
            nb.select(nb.find_cell_index(that));
        };
    });
};


// Subclasses must implement create_element.
Cell.prototype.create_element = function () {};


//============================================================================
// CodeCell
//============================================================================


var CodeCell = function (notebook) {
    Cell.apply(this, arguments);
    this.input_prompt_number = ' ';
    this.output_prompt_number = ' ';
};


CodeCell.prototype = new Cell();


CodeCell.prototype.create_element = function () {
    var cell =  $('<div></div>').addClass('cell code_cell')
    var input = $('<div></div>').addClass('input').append(
                    $('<div/>').addClass('prompt input_prompt')
                ).append(
                    $('<textarea/>').addClass('input_area').
                    attr('rows',1).
                    attr('cols',80).
                    attr('wrap','hard').
                    autoGrow()
                );
    var output = $('<div></div>').addClass('output').append(
                    $('<div/>').addClass('prompt output_prompt')
                ).append(
                    $('<div/>').addClass('output_area')
                );
    output.hide();
    cell.append(input).append(output);
    this.element = cell;
};


CodeCell.prototype.collapse = function () {
    this.element.find('div.output').hide();
};


CodeCell.prototype.expand = function () {
    this.element.find('div.output').show();
};


CodeCell.prototype.set_prompt = function (number) {
    this.set_input_prompt(number);
    this.set_output_prompt(number);
};

CodeCell.prototype.set_input_prompt = function (number) {
    var n = number || ' ';
    this.input_prompt_number = n
    this.element.find('div.input_prompt').html('In&nbsp;[' + n + ']:');
};


CodeCell.prototype.set_output_prompt = function (number) {
    var n = number || ' ';
    this.output_prompt_number = n
    this.element.find('div.output_prompt').html('Out[' + n + ']:');
};


//============================================================================
// TextCell
//============================================================================


var TextCell = function (notebook) {
    Cell.apply(this, arguments);
    this.placeholder = "Type <strong>HTML</strong> and LaTeX: $\\alpha^2$"
};


TextCell.prototype = new Cell();


TextCell.prototype.create_element = function () {
    var cell = $("<div>").addClass('cell text_cell').
               append(
                   $("<textarea>" + this.placeholder + "</textarea>").
                   addClass('text_cell_input').
                   attr('rows',1).
                   attr('cols',80).
                   autoGrow()
               ).append(
                   $('<div></div>').addClass('text_cell_render')
               )
    this.element = cell;
};


TextCell.prototype.select = function () {
    this.edit();
    Cell.prototype.select.apply(this);
};


TextCell.prototype.edit = function () {
    var text_cell = this.element;
    var input = text_cell.find("textarea.text_cell_input");
    var output = text_cell.find("div.text_cell_render");  
    output.hide();
    input.show().trigger('focus');
};


TextCell.prototype.render = function () {
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


//============================================================================
// On document ready
//============================================================================


var KernelManager = function () {
    this.kernelid = null;
    this.baseurl = "/kernels";
};


KernelManager.prototype.create_kernel = function () {
    var that = this;
    $.post(this.baseurl, function (data) {
        that.kernelid = data;
    }, 'json');
}


KernelManager.prototype.execute = function (code, callback) {
    var msg = {
        header : {msg_id : 0, username : "bgranger", session: 0},
        msg_type : "execute_request",
        content : {code : code}
    };
    var settings = {
      data : JSON.stringify(msg),
      processData : false,
      contentType : "application/json",
      success : callback,
      type : "POST"
    }
    var url = this.baseurl + "/" + this.kernelid + "/" + ""
}


//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

    MathJax.Hub.Config({
        tex2jax: {
            inlineMath: [ ['$','$'], ["\\(","\\)"] ],
            displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
        }
    });

    $("ul#main_menu").wijmenu({animation:{animated: "slide", duration: 100, easing: null}});
    IPYTHON.notebook = new Notebook('div.notebook');
    IPYTHON.notebook.insert_code_cell_after();

    $("#move_cell").buttonset();
    $("#move_up").button("option", "icons", {primary:"ui-icon-arrowthick-1-n"});
    $("#move_up").button("option", "text", false);
    $("#move_up").click(function () {IPYTHON.notebook.move_cell_up();});
    $("#move_down").button("option", "icons", {primary:"ui-icon-arrowthick-1-s"});
    $("#move_down").button("option", "text", false);
    $("#move_down").click(function () {IPYTHON.notebook.move_cell_down();});

    $("#insert_delete").buttonset();
    $("#insert_cell_before").click(function () {IPYTHON.notebook.insert_code_cell_before();});
    $("#insert_cell_after").click(function () {IPYTHON.notebook.insert_code_cell_after();});
    $("#delete_cell").button("option", "icons", {primary:"ui-icon-closethick"});
    $("#delete_cell").button("option", "text", false);
    $("#delete_cell").click(function () {IPYTHON.notebook.delete_cell();});

    $("#cell_type").buttonset();
    $("#to_code").click(function () {IPYTHON.notebook.text_to_code();});
    $("#to_text").click(function () {IPYTHON.notebook.code_to_text();});

    $("#sort").buttonset();
    $("#sort_cells").click(function () {IPYTHON.notebook.sort_cells();});

});