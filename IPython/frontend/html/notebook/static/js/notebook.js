
//============================================================================
// Notebook
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Notebook = function (selector) {
        this.element = $(selector);
        this.element.scroll();
        this.element.data("notebook", this);
        this.next_prompt_number = 1;
        this.kernel = null;
        this.msg_cell_map = {};
        this.filename = null;
        this.notebook_load_re = /%notebook load/
        this.notebook_save_re = /%notebook save/
        this.notebook_filename_re = /(\w)+.ipynb/
        this.style();
        this.create_elements();
        this.bind_events();
        this.start_kernel();
    };


    Notebook.prototype.style = function () {
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.create_elements = function () {
        // We add this end_space div to the end of the notebook div to:
        // i) provide a margin between the last cell and the end of the notebook
        // ii) to prevent the div from scrolling up when the last cell is being
        // edited, but is too low on the page, which browsers will do automatically.
        this.element.append($('<div class="end_space"></div>').height(50));
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.bind_events = function () {
        var that = this;
        $(document).keydown(function (event) {
            // console.log(event);
            if (event.which === 38) {
                var cell = that.selected_cell();
                if (cell.at_top()) {
                    event.preventDefault();
                    that.select_prev();
                };
            } else if (event.which === 40) {
                var cell = that.selected_cell();
                if (cell.at_bottom()) {
                    event.preventDefault();
                    that.select_next();
                };
            } else if (event.which === 13 && event.shiftKey) {
                console.log('Entering execute');
                that.execute_selected_cell(true);
                console.log('Leaving execute');
            };
        });

        this.element.bind('collapse_pager', function () {
            var app_height = $('div#notebook_app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var new_height = app_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, 'fast');
        });

        this.element.bind('expand_pager', function () {
            var app_height = $('div#notebook_app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var pager_height = $('div#pager').outerHeight(true);
            var new_height = app_height - pager_height - splitter_height; 
            that.element.animate({height : new_height + 'px'}, 'fast');
        });

        this.element.bind('collapse_left_panel', function () {
            var splitter_width = $('div#left_panel_splitter').outerWidth(true);
            var new_margin = splitter_width;
            $('div#notebook_panel').animate({marginLeft : new_margin + 'px'}, 'fast');
        });

        this.element.bind('expand_left_panel', function () {
            var splitter_width = $('div#left_panel_splitter').outerWidth(true);
            var left_panel_width = IPython.left_panel.width;
            var new_margin = splitter_width + left_panel_width;
            $('div#notebook_panel').animate({marginLeft : new_margin + 'px'}, 'fast');
        });
    };


    Notebook.prototype.scroll_to_bottom = function () {
        this.element.animate({scrollTop:this.element.get(0).scrollHeight}, 0);
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
            if (index === (this.ncells()-1)) {
                this.scroll_to_bottom();
            };
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
        this.element.find('div.end_space').before(cell.element);
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
        var cell = new IPython.CodeCell(this);
        cell.set_input_prompt(this.next_prompt_number);
        this.next_prompt_number = this.next_prompt_number + 1;
        this.insert_cell_before(cell, i);
        this.select(this.find_cell_index(cell));
        return this;
    }


    Notebook.prototype.insert_code_cell_after = function (index) {
        // TODO: Bounds check for i
        var i = this.index_or_selected(index);
        var cell = new IPython.CodeCell(this);
        cell.set_input_prompt(this.next_prompt_number);
        this.next_prompt_number = this.next_prompt_number + 1;
        this.insert_cell_after(cell, i);
        this.select(this.find_cell_index(cell));
        return this;
    }


    Notebook.prototype.insert_text_cell_before = function (index) {
        // TODO: Bounds check for i
        var i = this.index_or_selected(index);
        var cell = new IPython.TextCell(this);
        cell.config_mathjax();
        this.insert_cell_before(cell, i);
        this.select(this.find_cell_index(cell));
        return this;
    }


    Notebook.prototype.insert_text_cell_after = function (index) {
        // TODO: Bounds check for i
        var i = this.index_or_selected(index);
        var cell = new IPython.TextCell(this);
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
        if (source_cell instanceof IPython.TextCell) {
            this.insert_code_cell_after(i);
            var target_cell = this.cells()[i+1];
            target_cell.set_code(source_cell.get_text());
            source_element.remove();
        };
    };


    Notebook.prototype.code_to_text = function (index) {
        // TODO: Bounds check for i
        var i = this.index_or_selected(index);
        var source_element = this.cell_elements().eq(i);
        var source_cell = source_element.data("cell");
        if (source_cell instanceof IPython.CodeCell) {
            this.insert_text_cell_after(i);
            var target_cell = this.cells()[i+1];
            var text = source_cell.get_code();
            if (text === "") {text = target_cell.placeholder;};
            target_cell.set_text(text);
            source_element.remove();
            target_cell.edit();
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
        this.kernel = new IPython.Kernel();
        this.kernel.start_kernel($.proxy(this.kernel_started, this));
    };


    Notebook.prototype.handle_shell_reply = function (e) {
        reply = $.parseJSON(e.data);
        var header = reply.header;
        var content = reply.content;
        var msg_type = header.msg_type;
        // console.log(reply);
        var cell = this.cell_for_msg(reply.parent_header.msg_id);
        if (msg_type === "execute_reply") {
            cell.set_input_prompt(content.execution_count);
        };
        var payload = content.payload || [];
        this.handle_payload(content.payload);
    };


    Notebook.prototype.handle_payload = function (payload) {
        var l = payload.length;
        if (l > 0) {
            IPython.pager.clear();
            IPython.pager.expand();
        };
        for (var i=0; i<l; i++) {
            IPython.pager.append_text(payload[i].text);
        };
    };


    Notebook.prototype.handle_iopub_reply = function (e) {
        reply = $.parseJSON(e.data);
        var content = reply.content;
        // console.log(reply);
        var msg_type = reply.header.msg_type;
        var cell = this.cell_for_msg(reply.parent_header.msg_id);
        if (msg_type === "stream") {
            cell.expand();
            cell.append_stream(content.data + "\n");
        } else if (msg_type === "display_data") {
            cell.expand();
            cell.append_display_data(content.data);
        } else if (msg_type === "pyout") {
            cell.expand();
            cell.append_pyout(content.data, content.execution_count)
        } else if (msg_type === "pyerr") {
            cell.expand();
            cell.append_pyerr(content.ename, content.evalue, content.traceback);
        } else if (msg_type === "status") {
            if (content.execution_state === "busy") {
                IPython.kernel_status_widget.status_busy();
            } else if (content.execution_state === "idle") {
                IPython.kernel_status_widget.status_idle();
            };
        }
    };


    Notebook.prototype.kernel_started = function () {
        console.log("Kernel started: ", this.kernel.kernel_id);
        this.kernel.shell_channel.onmessage = $.proxy(this.handle_shell_reply,this);
        this.kernel.iopub_channel.onmessage = $.proxy(this.handle_iopub_reply,this);
    };


    Notebook.prototype.execute_selected_cell = function (add_new) {
        if (add_new === undefined) {add_new = true;};
        var that = this;
        var cell = that.selected_cell();
        var cell_index = that.find_cell_index(cell);
        // TODO: the logic here needs to be moved into appropriate
        // methods of Notebook.
        if (cell instanceof IPython.CodeCell) {
            cell.clear_output();
            var code = cell.get_code();
            if (that.notebook_load_re.test(code)) {
                var code_parts = code.split(' ');
                if (code_parts.length === 3) {
                    that.load_notebook(code_parts[2]);
                };
            } else if (that.notebook_save_re.test(code)) {
                var code_parts = code.split(' ');
                if (code_parts.length === 3) {
                    that.save_notebook(code_parts[2]);
                } else {
                    that.save_notebook()
                };
            } else {
                var msg_id = that.kernel.execute(cell.get_code());
                that.msg_cell_map[msg_id] = cell.cell_id;
            };
        } else if (cell instanceof IPython.TextCell) {
            cell.render();
        }
        if ((cell_index === (that.ncells()-1)) && add_new) {
            that.insert_code_cell_after();
            // If we are adding a new cell at the end, scroll down to show it.
            that.scroll_to_bottom();
        } else {
            that.select(cell_index+1);
        };
    };


    Notebook.prototype.execute_all_cells = function () {
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            this.select(i);
            this.execute_selected_cell(false);
        };
        this.scroll_to_bottom();
    };

    // Persistance and loading


    Notebook.prototype.fromJSON = function (data) {
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            // Always delete cell 0 as they get renumbered as they are deleted.
            this.delete_cell(0);
        };
        var new_cells = data.cells;
        ncells = new_cells.length;
        var cell_data = null;
        for (var i=0; i<ncells; i++) {
            cell_data = new_cells[i];
            if (cell_data.cell_type == 'code') {
                this.insert_code_cell_after();
                this.selected_cell().fromJSON(cell_data);
            } else if (cell_data.cell_type === 'text') {
                this.insert_text_cell_after();
                this.selected_cell().fromJSON(cell_data);
            };
        };
    };


    Notebook.prototype.toJSON = function () {
        var cells = this.cells();
        var ncells = cells.length;
        cell_array = new Array(ncells);
        for (var i=0; i<ncells; i++) {
            cell_array[i] = cells[i].toJSON();
        };
        json = {
            cells : cell_array
        };
        return json
    };


    Notebook.prototype.test_filename = function (filename) {
        if (this.notebook_filename_re.test(filename)) {
            return true;
        } else {
            var bad_filename = $('<div/>');
            bad_filename.html(
                "The filename you entered (" + filename + ") is not valid. Notebook filenames must have the following form: foo.ipynb"
            );
            bad_filename.dialog({title: 'Invalid filename', modal: true});
            return false;
        };
    };

    Notebook.prototype.save_notebook = function (filename) {
        this.filename = filename || this.filename || '';
        if (this.filename === '') {
            var no_filename = $('<div/>');
            no_filename.html(
                "This notebook has no filename, please specify a filename of the form: foo.ipynb"
            );
            no_filename.dialog({title: 'Missing filename', modal: true});
            return;
        }
        if (!this.test_filename(this.filename)) {return;}
        var thedata = this.toJSON();
        var settings = {
          processData : false,
          cache : false,
          type : "PUT",
          data : JSON.stringify(thedata),
          success : function (data, status, xhr) {console.log(data);}
        };
        $.ajax("/notebooks/" + this.filename, settings);
    };


    Notebook.prototype.load_notebook = function (filename) {
        if (!this.test_filename(filename)) {return;}
        var that = this;
        // We do the call with settings so we can set cache to false.
        var settings = {
          processData : false,
          cache : false,
          type : "GET",
          dataType : "json",
          success : function (data, status, xhr) {
              that.fromJSON(data);
              that.filename = filename;
              that.kernel.restart();
          }
        };
        $.ajax("/notebooks/" + filename, settings);
    }

    IPython.Notebook = Notebook;

    return IPython;

}(IPython));

