var IPYTHON = {};



// $.get("/notebooks/number2.nb",function (data, status, xhr) {console.log(data);});
// 
// settings = {
//   processData : false,
//   cache : false,
//   type : "DELETE",
//   success : function (data, status, xhr) {console.log(data);}
// }
// $.ajax("/notebooks/number2.nb",settings)
// 
// settings = {
//   processData : false,
//   cache : false,
//   type : "PUT",
//   success : function (data, status, xhr) {console.log(data);}
// }
// $.ajax("/notebooks/number2.nb",settings)


//============================================================================
// Utilities
//============================================================================


var uuid = function () {
    // http://www.ietf.org/rfc/rfc4122.txt
    var s = [];
    var hexDigits = "0123456789ABCDEF";
    for (var i = 0; i < 32; i++) {
        s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
    }
    s[12] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
    s[16] = hexDigits.substr((s[16] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01

    var uuid = s.join("");
    return uuid;
};


//Fix raw text to parse correctly in crazy XML
function xmlencode(string) {
    return string.replace(/\&/g,'&'+'amp;')
        .replace(/</g,'&'+'lt;')
        .replace(/>/g,'&'+'gt;')
        .replace(/\'/g,'&'+'apos;')
        .replace(/\"/g,'&'+'quot;')
        .replace(/`/g,'&'+'#96;')
}

//Map from terminal commands to CSS classes
attrib = {
    "30":"cblack", "31":"cred",
    "32":"cgreen", "33":"cyellow",  
    "34":"cblue", "36":"ccyan", 
    "37":"cwhite", "01":"cbold"}

//Fixes escaped console commands, IE colors. Turns them into HTML
function fixConsole(txt) {
    txt = xmlencode(txt)
    var re = /\033\[([\d;]*?)m/
    var opened = false
    var cmds = []
    var opener = ""
    var closer = ""
    
    while (re.test(txt)) {
        var cmds = txt.match(re)[1].split(";")
        closer = opened?"</span>":""
        opened = cmds.length > 1 || cmds[0] != 0
        var rep = []
        for (var i in cmds)
            if (typeof(attrib[cmds[i]]) != "undefined")
                rep.push(attrib[cmds[i]])
        opener = rep.length > 0?"<span class=\""+rep.join(" ")+"\">":""
        txt = txt.replace(re, closer + opener)
    }
    if (opened) txt += "</span>"
    return txt.trim()
}

//============================================================================
// Notebook
//============================================================================


var Notebook = function (selector) {
    this.element = $(selector);
    this.element.scroll();
    this.element.data("notebook", this);
    this.next_prompt_number = 1;
    this.next_kernel_number = 0;
    this.kernel = null;
    this.msg_cell_map = {};
    this.bind_events();
    this.start_kernel();
};


Notebook.prototype.bind_events = function () {
    var that = this;
    $(document).keydown(function (event) {
        // console.log(event);
        if (event.which == 38 && event.shiftKey) {
            event.preventDefault();
            that.select_prev();
        } else if (event.which == 40 && event.shiftKey) {
            event.preventDefault();
            that.select_next();
        } else if (event.which == 13 && event.shiftKey) {
            // The focus is not quite working here.
            var cell = that.selected_cell();
            var cell_index = that.find_cell_index(cell);
            if (cell instanceof CodeCell) {
                event.preventDefault();
                cell.clear_output();
                var msg_id = that.kernel.execute(cell.get_code());
                that.msg_cell_map[msg_id] = cell.cell_id;
                if (cell_index === (that.ncells()-1)) {
                    that.insert_code_cell_after();
                } else {
                    that.select(cell_index+1);
                };
            }
        } else if (event.which == 9) {
            event.preventDefault();
            var cell = that.selected_cell();
            if (cell instanceof CodeCell) {
                var ta = cell.element.find("textarea.input_area");
                ta.val(ta.val() + "    ");
            };
        };
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


Notebook.prototype.cell_for_msg = function (msg_id) {
    var cell_id = this.msg_cell_map[msg_id];
    var result = null;
    this.cell_elements().filter(function (index) {
        cell = $(this).data("cell");
        if (cell.cell_id === cell_id) {
            result = cell;
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
};


Notebook.prototype.expand = function (index) {
    var i = this.index_or_selected(index);
    this.cells()[i].expand();
};


// Kernel related things

Notebook.prototype.start_kernel = function () {
    this.kernel = new Kernel("kernel" + this.next_kernel_number);
    this.next_kernel_number = this.next_kernel_number + 1;
    this.kernel.start_kernel(this._kernel_started, this);
};


Notebook.prototype._kernel_started = function () {
    console.log("Kernel started: ", this.kernel.kernel_id);
    this.kernel.start_session(this._session_started, this);
};


Notebook.prototype._session_started = function () {
    console.log("Session started: ", this.kernel.session_id);
    var that = this;

    this.kernel.shell_channel.onmessage = function (e) {
        reply = $.parseJSON(e.data);
        console.log(reply);
        var msg_type = reply.msg_type;
        var cell = that.cell_for_msg(reply.parent_header.msg_id);
        if (msg_type === "execute_reply") {
            cell.set_prompt(reply.content.execution_count);
        };
    };

    this.kernel.iopub_channel.onmessage = function (e) {
        reply = $.parseJSON(e.data);
        console.log(reply);
        var msg_type = reply.msg_type;
        var cell = that.cell_for_msg(reply.parent_header.msg_id);
        if (msg_type === "stream") {
            cell.expand();
            cell.append_stream(reply.content.data + "\n");
        } else if (msg_type === "pyout" || msg_type === "display_data") {
            cell.expand();
            cell.append_display_data(reply.content.data);
        };
    };
};


Notebook.prototype._handle_execute_reply = function (reply, cell) {
    cell.set_prompt(reply.content.execution_count);
};


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
    this.cell_id = uuid();
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
    cell.append(input).append(output);
    this.element = cell;
    this.collapse()
};


CodeCell.prototype.append_stream = function (data) {
    var data_list = data.split("\n");
    console.log(data_list);
    if (data_list.length > 0) {
        for (var i=0; i<data_list.length; i++) {
            console.log(i, data_list[i]);
            var toinsert = fixConsole(data_list[i]);
            this.element.find("div.output_area").append($("<p>").append(toinsert));
        };
    }
};


CodeCell.prototype.append_display_data = function (data) {
    if (data["image/svg+xml"] !== undefined) {
        this.append_svg(data["image/svg+xml"]);
    } else if (data["text/plain"] !== undefined) {
        console.log(data["text/plain"]);
        this.append_stream(data["text/plain"]);
    };
};

CodeCell.prototype.append_svg = function (svg) {
    this.element.find("div.output_area").append(svg);
};


CodeCell.prototype.clear_output = function () {
    this.element.find("div.output_area").html("");
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


CodeCell.prototype.get_code = function () {
    return this.element.find("textarea.input_area").val();
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


var Kernel = function (kernel_id) {
    this.kernel_id = kernel_id;
    this.base_url = "/kernels";
    this.kernel_url = this.base_url + "/" + this.kernel_id
    this.session_id = null;
};


Kernel.prototype.get_msg = function (msg_type, content) {
    var msg = {
        header : {
            msg_id : uuid(),
            username : "bgranger",
            session: this.session_id
        },
        msg_type : msg_type,
        content : content,
        parent_header : {}
    };
    return msg;
}

Kernel.prototype.start_kernel = function (callback, context) {
    $.post(this.kernel_url, function () {
        callback.call(context);
    });
};


Kernel.prototype.start_session = function (callback, context) {
    var that = this;
    $.post(this.kernel_url + "/sessions",
        function (session_id) {
            that._handle_start_session(session_id, callback, context);
        },
        'json');
}


Kernel.prototype._handle_start_session = function (session_id, callback, context) {
    this.session_id = session_id;
    this.session_url = this.kernel_url + "/sessions/" + this.session_id;
    this._start_channels();
    callback.call(context);
};


Kernel.prototype._start_channels = function () {
    var ws_url = "ws://127.0.0.1:8888" + this.session_url;
    this.shell_channel = new WebSocket(ws_url + "/shell");
    this.iopub_channel = new WebSocket(ws_url + "/iopub");
}


Kernel.prototype.execute = function (code) {
    var content = {
        code : code,
        silent : false,
        user_variables : [],
        user_expressions : {}
    };
    var msg = this.get_msg("execute_request", content);

    this.shell_channel.send(JSON.stringify(msg));
    return msg.header.msg_id;
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

    $("#toggle").buttonset();
    $("#collapse").click(function () {IPYTHON.notebook.collapse();});
    $("#expand").click(function () {IPYTHON.notebook.expand();});

});