//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notebook
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;
    var key   = IPython.utils.keycodes;

    var Notebook = function (selector) {
        this.read_only = IPython.read_only;
        this.element = $(selector);
        this.element.scroll();
        this.element.data("notebook", this);
        this.next_prompt_number = 1;
        this.kernel = null;
        this.clipboard = null;
        this.paste_enabled = false;
        this.dirty = false;
        this.metadata = {};
        // single worksheet for now
        this.worksheet_metadata = {};
        this.control_key_active = false;
        this.notebook_id = null;
        this.notebook_name = null;
        this.notebook_name_blacklist_re = /[\/\\:]/;
        this.nbformat = 3 // Increment this when changing the nbformat
        this.nbformat_minor = 0 // Increment this when changing the nbformat
        this.style();
        this.create_elements();
        this.bind_events();
    };


    Notebook.prototype.style = function () {
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.create_elements = function () {
        // We add this end_space div to the end of the notebook div to:
        // i) provide a margin between the last cell and the end of the notebook
        // ii) to prevent the div from scrolling up when the last cell is being
        // edited, but is too low on the page, which browsers will do automatically.
        var that = this;
        var end_space = $('<div/>').addClass('end_space').height("30%");
        end_space.dblclick(function (e) {
            if (that.read_only) return;
            var ncells = that.ncells();
            that.insert_cell_below('code',ncells-1);
        });
        this.element.append(end_space);
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.bind_events = function () {
        var that = this;

        $([IPython.events]).on('set_next_input.Notebook', function (event, data) {
            var index = that.find_cell_index(data.cell);
            var new_cell = that.insert_cell_below('code',index);
            new_cell.set_text(data.text);
            that.dirty = true;
        });

        $([IPython.events]).on('set_dirty.Notebook', function (event, data) {
            that.dirty = data.value;
        });

        $([IPython.events]).on('select.Cell', function (event, data) {
            var index = that.find_cell_index(data.cell);
            that.select(index);
        });


        $(document).keydown(function (event) {
            // console.log(event);
            if (that.read_only) return true;
            
            // Save (CTRL+S) or (AppleKey+S) 
            //metaKey = applekey on mac
            if ((event.ctrlKey || event.metaKey) && event.keyCode==83) { 
                that.save_notebook();
                event.preventDefault();
                return false;
            } else if (event.which === key.ESC) {
                // Intercept escape at highest level to avoid closing 
                // websocket connection with firefox
                event.preventDefault();
            } else if (event.which === key.SHIFT) {
                // ignore shift keydown
                return true;
            }
            if (event.which === key.UPARROW && !event.shiftKey) {
                var cell = that.get_selected_cell();
                if (cell.at_top()) {
                    event.preventDefault();
                    that.select_prev();
                };
            } else if (event.which === key.DOWNARROW && !event.shiftKey) {
                var cell = that.get_selected_cell();
                if (cell.at_bottom()) {
                    event.preventDefault();
                    that.select_next();
                };
            } else if (event.which === key.ENTER && event.shiftKey) {
                that.execute_selected_cell();
                return false;
            } else if (event.which === key.ENTER && event.ctrlKey) {
                that.execute_selected_cell({terminal:true});
                return false;
            } else if (event.which === 77 && event.ctrlKey && that.control_key_active == false) {
                that.control_key_active = true;
                return false;
            } else if (event.which === 88 && that.control_key_active) {
                // Cut selected cell = x
                that.cut_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 67 && that.control_key_active) {
                // Copy selected cell = c
                that.copy_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 86 && that.control_key_active) {
                // Paste selected cell = v
                that.paste_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 68 && that.control_key_active) {
                // Delete selected cell = d
                that.delete_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 65 && that.control_key_active) {
                // Insert code cell above selected = a
                that.insert_cell_above('code');
                that.control_key_active = false;
                return false;
            } else if (event.which === 66 && that.control_key_active) {
                // Insert code cell below selected = b
                that.insert_cell_below('code');
                that.control_key_active = false;
                return false;
            } else if (event.which === 89 && that.control_key_active) {
                // To code = y
                that.to_code();
                that.control_key_active = false;
                return false;
            } else if (event.which === 77 && that.control_key_active) {
                // To markdown = m
                that.to_markdown();
                that.control_key_active = false;
                return false;
            } else if (event.which === 84 && that.control_key_active) {
                // To Raw = t
                that.to_raw();
                that.control_key_active = false;
                return false;
            } else if (event.which === 49 && that.control_key_active) {
                // To Heading 1 = 1
                that.to_heading(undefined, 1);
                that.control_key_active = false;
                return false;
            } else if (event.which === 50 && that.control_key_active) {
                // To Heading 2 = 2
                that.to_heading(undefined, 2);
                that.control_key_active = false;
                return false;
            } else if (event.which === 51 && that.control_key_active) {
                // To Heading 3 = 3
                that.to_heading(undefined, 3);
                that.control_key_active = false;
                return false;
            } else if (event.which === 52 && that.control_key_active) {
                // To Heading 4 = 4
                that.to_heading(undefined, 4);
                that.control_key_active = false;
                return false;
            } else if (event.which === 53 && that.control_key_active) {
                // To Heading 5 = 5
                that.to_heading(undefined, 5);
                that.control_key_active = false;
                return false;
            } else if (event.which === 54 && that.control_key_active) {
                // To Heading 6 = 6
                that.to_heading(undefined, 6);
                that.control_key_active = false;
                return false;
            } else if (event.which === 79 && that.control_key_active) {
                // Toggle output = o
                if (event.shiftKey){
                    that.toggle_output_scroll();
                } else {
                    that.toggle_output();
                }
                that.control_key_active = false;
                return false;
            } else if (event.which === 83 && that.control_key_active) {
                // Save notebook = s
                that.save_notebook();
                that.control_key_active = false;
                return false;
            } else if (event.which === 74 && that.control_key_active) {
                // Move cell down = j
                that.move_cell_down();
                that.control_key_active = false;
                return false;
            } else if (event.which === 75 && that.control_key_active) {
                // Move cell up = k
                that.move_cell_up();
                that.control_key_active = false;
                return false;
            } else if (event.which === 80 && that.control_key_active) {
                // Select previous = p
                that.select_prev();
                that.control_key_active = false;
                return false;
            } else if (event.which === 78 && that.control_key_active) {
                // Select next = n
                that.select_next();
                that.control_key_active = false;
                return false;
            } else if (event.which === 76 && that.control_key_active) {
                // Toggle line numbers = l
                that.cell_toggle_line_numbers();
                that.control_key_active = false;
                return false;
            } else if (event.which === 73 && that.control_key_active) {
                // Interrupt kernel = i
                that.kernel.interrupt();
                that.control_key_active = false;
                return false;
            } else if (event.which === 190 && that.control_key_active) {
                // Restart kernel = .  # matches qt console
                that.restart_kernel();
                that.control_key_active = false;
                return false;
            } else if (event.which === 72 && that.control_key_active) {
                // Show keyboard shortcuts = h
                IPython.quick_help.show_keyboard_shortcuts();
                that.control_key_active = false;
                return false;
            } else if (that.control_key_active) {
                that.control_key_active = false;
                return true;
            };
            return true;
        });

        var collapse_time = function(time){
            var app_height = $('div#main_app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var new_height = app_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, time);
        }

        this.element.bind('collapse_pager', function (event,extrap) {
            time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            collapse_time(time);
        });

        var expand_time = function(time) {
            var app_height = $('div#main_app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var pager_height = $('div#pager').outerHeight(true);
            var new_height = app_height - pager_height - splitter_height; 
            that.element.animate({height : new_height + 'px'}, time);
        }

        this.element.bind('expand_pager', function (event, extrap) {
            time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            expand_time(time);
        });

        $(window).bind('beforeunload', function () {
            // TODO: Make killing the kernel configurable.
            var kill_kernel = false;
            if (kill_kernel) {
                that.kernel.kill();
            }
            if (that.dirty && ! that.read_only) {
                return "You have unsaved changes that will be lost if you leave this page.";
            };
            // Null is the *only* return value that will make the browser not
            // pop up the "don't leave" dialog.
            return null;
        });
    };


    Notebook.prototype.scroll_to_bottom = function () {
        this.element.animate({scrollTop:this.element.get(0).scrollHeight}, 0);
    };


    Notebook.prototype.scroll_to_top = function () {
        this.element.animate({scrollTop:0}, 0);
    };


    // Cell indexing, retrieval, etc.

    Notebook.prototype.get_cell_elements = function () {
        return this.element.children("div.cell");
    };


    Notebook.prototype.get_cell_element = function (index) {
        var result = null;
        var e = this.get_cell_elements().eq(index);
        if (e.length !== 0) {
            result = e;
        }
        return result;
    };


    Notebook.prototype.ncells = function (cell) {
        return this.get_cell_elements().length;
    };


    // TODO: we are often calling cells as cells()[i], which we should optimize
    // to cells(i) or a new method.
    Notebook.prototype.get_cells = function () {
        return this.get_cell_elements().toArray().map(function (e) {
            return $(e).data("cell");
        });
    };


    Notebook.prototype.get_cell = function (index) {
        var result = null;
        var ce = this.get_cell_element(index);
        if (ce !== null) {
            result = ce.data('cell');
        }
        return result;
    }


    Notebook.prototype.get_next_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index < this.ncells()) {
            result = this.get_cell(index+1);
        }
        return result;
    }


    Notebook.prototype.get_prev_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index > 1) {
            result = this.get_cell(index-1);
        }
        return result;
    }

    Notebook.prototype.find_cell_index = function (cell) {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell") === cell) {
                result = index;
            };
        });
        return result;
    };


    Notebook.prototype.index_or_selected = function (index) {
        var i;
        if (index === undefined || index === null) {
            i = this.get_selected_index();
            if (i === null) {
                i = 0;
            }
        } else {
            i = index;
        }
        return i;
    };


    Notebook.prototype.get_selected_cell = function () {
        var index = this.get_selected_index();
        return this.get_cell(index);
    };


    Notebook.prototype.is_valid_cell_index = function (index) {
        if (index !== null && index >= 0 && index < this.ncells()) {
            return true;
        } else {
            return false;
        };
    }

    Notebook.prototype.get_selected_index = function () {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell").selected === true) {
                result = index;
            };
        });
        return result;
    };


    // Cell selection.

    Notebook.prototype.select = function (index) {
        if (index !== undefined && index >= 0 && index < this.ncells()) {
            sindex = this.get_selected_index()
            if (sindex !== null && index !== sindex) {
                this.get_cell(sindex).unselect();
            };
            var cell = this.get_cell(index)
            cell.select();
            if (cell.cell_type === 'heading') {
                $([IPython.events]).trigger('selected_cell_type_changed.Notebook',
                    {'cell_type':cell.cell_type,level:cell.level}
                );
            } else {
                $([IPython.events]).trigger('selected_cell_type_changed.Notebook',
                    {'cell_type':cell.cell_type}
                );
            };
        };
        return this;
    };


    Notebook.prototype.select_next = function () {
        var index = this.get_selected_index();
        if (index !== null && index >= 0 && (index+1) < this.ncells()) {
            this.select(index+1);
        };
        return this;
    };


    Notebook.prototype.select_prev = function () {
        var index = this.get_selected_index();
        if (index !== null && index >= 0 && (index-1) < this.ncells()) {
            this.select(index-1);
        };
        return this;
    };


    // Cell movement

    Notebook.prototype.move_cell_up = function (index) {
        var i = this.index_or_selected();
        if (i !== null && i < this.ncells() && i > 0) {
            var pivot = this.get_cell_element(i-1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.before(tomove);
                this.select(i-1);
            };
        };
        this.dirty = true;
        return this;
    };


    Notebook.prototype.move_cell_down = function (index) {
        var i = this.index_or_selected();
        if (i !== null && i < (this.ncells()-1) && i >= 0) {
            var pivot = this.get_cell_element(i+1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.after(tomove);
                this.select(i+1);
            };
        };
        this.dirty = true;
        return this;
    };


    Notebook.prototype.sort_cells = function () {
        // This is not working right now. Calling this will actually crash
        // the browser. I think there is an infinite loop in here...
        var ncells = this.ncells();
        var sindex = this.get_selected_index();
        var swapped;
        do {
            swapped = false;
            for (var i=1; i<ncells; i++) {
                current = this.get_cell(i);
                previous = this.get_cell(i-1);
                if (previous.input_prompt_number > current.input_prompt_number) {
                    this.move_cell_up(i);
                    swapped = true;
                };
            };
        } while (swapped);
        this.select(sindex);
        return this;
    };

    // Insertion, deletion.

    Notebook.prototype.delete_cell = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var ce = this.get_cell_element(i);
            ce.remove();
            if (i === (this.ncells())) {
                this.select(i-1);
            } else {
                this.select(i);
            };
            this.dirty = true;
        };
        return this;
    };


    Notebook.prototype.insert_cell_below = function (type, index) {
        // type = ('code','html','markdown')
        // index = cell index or undefined to insert below selected
        index = this.index_or_selected(index);
        var cell = null;
        if (this.ncells() === 0 || this.is_valid_cell_index(index)) {
            if (type === 'code') {
                cell = new IPython.CodeCell(this.kernel);
                cell.set_input_prompt();
            } else if (type === 'markdown') {
                cell = new IPython.MarkdownCell();
            } else if (type === 'html') {
                cell = new IPython.HTMLCell();
            } else if (type === 'raw') {
                cell = new IPython.RawCell();
            } else if (type === 'heading') {
                cell = new IPython.HeadingCell();
            };
            if (cell !== null) {
                if (this.ncells() === 0) {
                    this.element.find('div.end_space').before(cell.element);
                } else if (this.is_valid_cell_index(index)) {
                    this.get_cell_element(index).after(cell.element);
                };
                cell.render();
                this.select(this.find_cell_index(cell));
                this.dirty = true;
                return cell;
            };
        };
        return cell;
    };


    Notebook.prototype.insert_cell_above = function (type, index) {
        // type = ('code','html','markdown')
        // index = cell index or undefined to insert above selected
        index = this.index_or_selected(index);
        var cell = null;
        if (this.ncells() === 0 || this.is_valid_cell_index(index)) {
            if (type === 'code') {
                cell = new IPython.CodeCell(this.kernel);
                cell.set_input_prompt();
            } else if (type === 'markdown') {
                cell = new IPython.MarkdownCell();
            } else if (type === 'html') {
                cell = new IPython.HTMLCell();
            } else if (type === 'raw') {
                cell = new IPython.RawCell();
            } else if (type === 'heading') {
                cell = new IPython.HeadingCell();
            };
            if (cell !== null) {
                if (this.ncells() === 0) {
                    this.element.find('div.end_space').before(cell.element);
                } else if (this.is_valid_cell_index(index)) {
                    this.get_cell_element(index).before(cell.element);
                };
                cell.render();
                this.select(this.find_cell_index(cell));
                this.dirty = true;
                return cell;
            };
        };
        return cell;
    };


    Notebook.prototype.to_code = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            if (!(source_cell instanceof IPython.CodeCell)) {
                target_cell = this.insert_cell_below('code',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                }
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.dirty = true;
            };
        };
    };


    Notebook.prototype.to_markdown = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            if (!(source_cell instanceof IPython.MarkdownCell)) {
                target_cell = this.insert_cell_below('markdown',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                };
                // The edit must come before the set_text.
                target_cell.edit();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.dirty = true;
            };
        };
    };


    Notebook.prototype.to_html = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            var target_cell = null;
            if (!(source_cell instanceof IPython.HTMLCell)) {
                target_cell = this.insert_cell_below('html',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                };
                // The edit must come before the set_text.
                target_cell.edit();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.dirty = true;
            };
        };
    };


    Notebook.prototype.to_raw = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            var target_cell = null;
            if (!(source_cell instanceof IPython.RawCell)) {
                target_cell = this.insert_cell_below('raw',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                };
                // The edit must come before the set_text.
                target_cell.edit();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.dirty = true;
            };
        };
    };


    Notebook.prototype.to_heading = function (index, level) {
        level = level || 1;
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            var target_cell = null;
            if (source_cell instanceof IPython.HeadingCell) {
                source_cell.set_level(level);
            } else {
                target_cell = this.insert_cell_below('heading',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                };
                // The edit must come before the set_text.
                target_cell.set_level(level);
                target_cell.edit();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.dirty = true;
            };
            $([IPython.events]).trigger('selected_cell_type_changed.Notebook',
                {'cell_type':'heading',level:level}
            );
        };
    };


    // Cut/Copy/Paste

    Notebook.prototype.enable_paste = function () {
        var that = this;
        if (!this.paste_enabled) {
            $('#paste_cell').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell();});
            $('#paste_cell_above').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell_above();});
            $('#paste_cell_below').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell_below();});
            this.paste_enabled = true;
        };
    };


    Notebook.prototype.disable_paste = function () {
        if (this.paste_enabled) {
            $('#paste_cell').addClass('ui-state-disabled').off('click');
            $('#paste_cell_above').addClass('ui-state-disabled').off('click');
            $('#paste_cell_below').addClass('ui-state-disabled').off('click');
            this.paste_enabled = false;
        };
    };


    Notebook.prototype.cut_cell = function () {
        this.copy_cell();
        this.delete_cell();
    }

    Notebook.prototype.copy_cell = function () {
        var cell = this.get_selected_cell();
        this.clipboard = cell.toJSON();
        this.enable_paste();
    };


    Notebook.prototype.paste_cell = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            old_cell = this.get_next_cell(new_cell);
            this.delete_cell(this.find_cell_index(old_cell));
            this.select(this.find_cell_index(new_cell));
        };
    };


    Notebook.prototype.paste_cell_above = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };


    Notebook.prototype.paste_cell_below = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_below(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };


    // Split/merge

    Notebook.prototype.split_cell = function () {
        // Todo: implement spliting for other cell types.
        var cell = this.get_selected_cell();
        if (cell.is_splittable()) {
            texta = cell.get_pre_cursor();
            textb = cell.get_post_cursor();
            if (cell instanceof IPython.CodeCell) {
                cell.set_text(texta);
                var new_cell = this.insert_cell_below('code');
                new_cell.set_text(textb);
            } else if (cell instanceof IPython.MarkdownCell) {
                cell.set_text(texta);
                cell.render();
                var new_cell = this.insert_cell_below('markdown');
                new_cell.edit(); // editor must be visible to call set_text
                new_cell.set_text(textb);
                new_cell.render();
            } else if (cell instanceof IPython.HTMLCell) {
                cell.set_text(texta);
                cell.render();
                var new_cell = this.insert_cell_below('html');
                new_cell.edit(); // editor must be visible to call set_text
                new_cell.set_text(textb);
                new_cell.render();
            };
        };
    };


    Notebook.prototype.merge_cell_above = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        if (index > 0) {
            upper_cell = this.get_cell(index-1);
            upper_text = upper_cell.get_text();
            text = cell.get_text();
            if (cell instanceof IPython.CodeCell) {
                cell.set_text(upper_text+'\n'+text);
            } else if (cell instanceof IPython.MarkdownCell || cell instanceof IPython.HTMLCell) {
                cell.edit();
                cell.set_text(upper_text+'\n'+text);
                cell.render();
            };
            this.delete_cell(index-1);
            this.select(this.find_cell_index(cell));
        };
    };


    Notebook.prototype.merge_cell_below = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        if (index < this.ncells()-1) {
            lower_cell = this.get_cell(index+1);
            lower_text = lower_cell.get_text();
            text = cell.get_text();
            if (cell instanceof IPython.CodeCell) {
                cell.set_text(text+'\n'+lower_text);
            } else if (cell instanceof IPython.MarkdownCell || cell instanceof IPython.HTMLCell) {
                cell.edit();
                cell.set_text(text+'\n'+lower_text);
                cell.render();
            };
            this.delete_cell(index+1);
            this.select(this.find_cell_index(cell));
        };
    };


    // Cell collapsing and output clearing

    Notebook.prototype.collapse = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).collapse();
        this.dirty = true;
    };


    Notebook.prototype.expand = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).expand();
        this.dirty = true;
    };


    Notebook.prototype.toggle_output = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output();
        this.dirty = true;
    };


    Notebook.prototype.toggle_output_scroll = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output_scroll();
    };


    Notebook.prototype.collapse_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].output_area.collapse();
            }
        };
        // this should not be set if the `collapse` key is removed from nbformat
        this.dirty = true;
    };


    Notebook.prototype.scroll_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].output_area.expand();
                cells[i].output_area.scroll_if_long(20);
            }
        };
        // this should not be set if the `collapse` key is removed from nbformat
        this.dirty = true;
    };


    Notebook.prototype.expand_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].output_area.expand();
                cells[i].output_area.unscroll_area();
            }
        };
        // this should not be set if the `collapse` key is removed from nbformat
        this.dirty = true;
    };


    Notebook.prototype.clear_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].clear_output(true,true,true);
                // Make all In[] prompts blank, as well
                // TODO: make this configurable (via checkbox?)
                cells[i].set_input_prompt();
            }
        };
        this.dirty = true;
    };


    // Other cell functions: line numbers, ...

    Notebook.prototype.cell_toggle_line_numbers = function() {
        this.get_selected_cell().toggle_line_numbers();
    };

    // Kernel related things

    Notebook.prototype.start_kernel = function () {
        var base_url = $('body').data('baseKernelUrl') + "kernels";
        this.kernel = new IPython.Kernel(base_url);
        this.kernel.start(this.notebook_id);
        // Now that the kernel has been created, tell the CodeCells about it.
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            var cell = this.get_cell(i);
            if (cell instanceof IPython.CodeCell) {
                cell.set_kernel(this.kernel)
            };
        };
    };


    Notebook.prototype.restart_kernel = function () {
        var that = this;
        var dialog = $('<div/>');
        dialog.html('Do you want to restart the current kernel?  You will lose all variables defined in it.');
        $(document).append(dialog);
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Restart kernel or continue running?",
            closeText: '',
            buttons : {
                "Restart": function () {
                    that.kernel.restart();
                    $(this).dialog('close');
                },
                "Continue running": function () {
                    $(this).dialog('close');
                }
            }
        });
    };


    Notebook.prototype.execute_selected_cell = function (options) {
        // add_new: should a new cell be added if we are at the end of the nb
        // terminal: execute in terminal mode, which stays in the current cell
        default_options = {terminal: false, add_new: true};
        $.extend(default_options, options);
        var that = this;
        var cell = that.get_selected_cell();
        var cell_index = that.find_cell_index(cell);
        if (cell instanceof IPython.CodeCell) {
            cell.execute();
        } else if (cell instanceof IPython.HTMLCell) {
            cell.render();
        }
        if (default_options.terminal) {
            cell.select_all();
        } else {
            if ((cell_index === (that.ncells()-1)) && default_options.add_new) {
                that.insert_cell_below('code');
                // If we are adding a new cell at the end, scroll down to show it.
                that.scroll_to_bottom();
            } else {
                that.select(cell_index+1);
            };
        };
        this.dirty = true;
    };


    Notebook.prototype.execute_all_cells = function () {
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            this.select(i);
            this.execute_selected_cell({add_new:false});
        };
        this.scroll_to_bottom();
    };

    // Persistance and loading

    Notebook.prototype.get_notebook_id = function () {
        return this.notebook_id;
    };


    Notebook.prototype.get_notebook_name = function () {
        return this.notebook_name;
    };


    Notebook.prototype.set_notebook_name = function (name) {
        this.notebook_name = name;
    };


    Notebook.prototype.test_notebook_name = function (nbname) {
        nbname = nbname || '';
        if (this.notebook_name_blacklist_re.test(nbname) == false && nbname.length>0) {
            return true;
        } else {
            return false;
        };
    };


    Notebook.prototype.fromJSON = function (data) {
        var ncells = this.ncells();
        var i;
        for (i=0; i<ncells; i++) {
            // Always delete cell 0 as they get renumbered as they are deleted.
            this.delete_cell(0);
        };
        // Save the metadata and name.
        this.metadata = data.metadata;
        this.notebook_name = data.metadata.name;
        // Only handle 1 worksheet for now.
        var worksheet = data.worksheets[0];
        if (worksheet !== undefined) {
            if (worksheet.metadata) {
                this.worksheet_metadata = worksheet.metadata;
            }
            var new_cells = worksheet.cells;
            ncells = new_cells.length;
            var cell_data = null;
            var new_cell = null;
            for (i=0; i<ncells; i++) {
                cell_data = new_cells[i];
                // VERSIONHACK: plaintext -> raw
                // handle never-released plaintext name for raw cells
                if (cell_data.cell_type === 'plaintext'){
                    cell_data.cell_type = 'raw';
                }
                
                new_cell = this.insert_cell_below(cell_data.cell_type);
                new_cell.fromJSON(cell_data);
            };
        };
        if (data.worksheets.length > 1) {
            var dialog = $('<div/>');
            dialog.html("This notebook has " + data.worksheets.length + " worksheets, " +
            "but this version of IPython can only handle the first.  " +
            "If you save this notebook, worksheets after the first will be lost."
            );
            this.element.append(dialog);
            dialog.dialog({
                resizable: false,
                modal: true,
                title: "Multiple worksheets",
                closeText: "",
                close: function(event, ui) {$(this).dialog('destroy').remove();},
                buttons : {
                    "OK": function () {
                        $(this).dialog('close');
                    }
                },
                width: 400
            });
        }
    };


    Notebook.prototype.toJSON = function () {
        var cells = this.get_cells();
        var ncells = cells.length;
        var cell_array = new Array(ncells);
        for (var i=0; i<ncells; i++) {
            cell_array[i] = cells[i].toJSON();
        };
        var data = {
            // Only handle 1 worksheet for now.
            worksheets : [{
                cells: cell_array,
                metadata: this.worksheet_metadata
            }],
            metadata : this.metadata
        };
        return data;
    };

    Notebook.prototype.save_notebook = function () {
        // We may want to move the name/id/nbformat logic inside toJSON?
        var data = this.toJSON();
        data.metadata.name = this.notebook_name;
        data.nbformat = this.nbformat;
        data.nbformat_minor = this.nbformat_minor;
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "PUT",
            data : JSON.stringify(data),
            headers : {'Content-Type': 'application/json'},
            success : $.proxy(this.save_notebook_success,this),
            error : $.proxy(this.save_notebook_error,this)
        };
        $([IPython.events]).trigger('notebook_saving.Notebook');
        var url = $('body').data('baseProjectUrl') + 'notebooks/' + this.notebook_id;
        $.ajax(url, settings);
    };


    Notebook.prototype.save_notebook_success = function (data, status, xhr) {
        this.dirty = false;
        $([IPython.events]).trigger('notebook_saved.Notebook');
    };


    Notebook.prototype.save_notebook_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('notebook_save_failed.Notebook');
    };


    Notebook.prototype.load_notebook = function (notebook_id) {
        var that = this;
        this.notebook_id = notebook_id;
        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.load_notebook_success,this),
            error : $.proxy(this.load_notebook_error,this),
        };
        $([IPython.events]).trigger('notebook_loading.Notebook');
        var url = $('body').data('baseProjectUrl') + 'notebooks/' + this.notebook_id;
        $.ajax(url, settings);
    };


    Notebook.prototype.load_notebook_success = function (data, status, xhr) {
        this.fromJSON(data);
        if (this.ncells() === 0) {
            this.insert_cell_below('code');
        };
        this.dirty = false;
        this.select(0);
        this.scroll_to_top();
        if (data.orig_nbformat !== undefined && data.nbformat !== data.orig_nbformat) {
            msg = "This notebook has been converted from an older " +
            "notebook format (v"+data.orig_nbformat+") to the current notebook " +
            "format (v"+data.nbformat+"). The next time you save this notebook, the " +
            "newer notebook format will be used and older verions of IPython " +
            "may not be able to read it. To keep the older version, close the " +
            "notebook without saving it.";
            var dialog = $('<div/>');
            dialog.html(msg);
            this.element.append(dialog);
            dialog.dialog({
                resizable: false,
                modal: true,
                title: "Notebook converted",
                closeText: "",
                close: function(event, ui) {$(this).dialog('destroy').remove();},
                buttons : {
                    "OK": function () {
                        $(this).dialog('close');
                    }
                },
                width: 400
            });
        } else if (data.orig_nbformat_minor !== undefined && data.nbformat_minor !== data.orig_nbformat_minor) {
            var that = this;
            var orig_vs = 'v' + data.nbformat + '.' + data.orig_nbformat_minor;
            var this_vs = 'v' + data.nbformat + '.' + this.nbformat_minor;
            msg = "This notebook is version " + orig_vs + ", but we only fully support up to " +
            this_vs + ".  You can still work with this notebook, but some features " +
            "introduced in later notebook versions may not be available."
            
            var dialog = $('<div/>');
            dialog.html(msg);
            this.element.append(dialog);
            dialog.dialog({
                resizable: false,
                modal: true,
                title: "Newer Notebook",
                closeText: "",
                close: function(event, ui) {$(this).dialog('destroy').remove();},
                buttons : {
                    "OK": function () {
                        $(this).dialog('close');
                    }
                },
                width: 400
            });
            
        }
        // Create the kernel after the notebook is completely loaded to prevent
        // code execution upon loading, which is a security risk.
        if (! this.read_only) {
            this.start_kernel();
        }
        $([IPython.events]).trigger('notebook_loaded.Notebook');
    };


    Notebook.prototype.load_notebook_error = function (xhr, textStatus, errorThrow) {
        if (xhr.status === 500) {
            msg = "An error occurred while loading this notebook. Most likely " +
            "this notebook is in a newer format than is supported by this " +
            "version of IPython. This version can load notebook formats " +
            "v"+this.nbformat+" or earlier.";
            var dialog = $('<div/>');
            dialog.html(msg);
            this.element.append(dialog);
            dialog.dialog({
                resizable: false,
                modal: true,
                title: "Error loading notebook",
                closeText: "",
                close: function(event, ui) {$(this).dialog('destroy').remove();},
                buttons : {
                    "OK": function () {
                        $(this).dialog('close');
                    }
                },
                width: 400
            });
        }
    }
    
    IPython.Notebook = Notebook;


    return IPython;

}(IPython));

