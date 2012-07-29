//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Worksheet
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;
    var key   = IPython.utils.keycodes;

    var Worksheet = function (element, name, kernel) {
        this.read_only = IPython.read_only;
        this.element = element;
        this.element.data("worksheet", this);
        this.next_prompt_number = 1;
        this.kernel = kernel;
        this.clipboard = null;
        this.paste_enabled = false;
        this.dirty = false;
        this.metadata = {name: name};
        this.style();
	this.worksheet_id = this.element.attr('id');
        this.create_elements();
        this.bind_events();
    };


    Worksheet.prototype.style = function () {
    };

    Worksheet.prototype.create_elements = function () {
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
    };


    Worksheet.prototype.bind_events = function () {
	var that = this;

        $([IPython.events]).on('set_next_input.Worksheet', function (event, data) {
            var index = that.find_cell_index(data.cell);
            var new_cell = that.insert_cell_below('code',index);
            new_cell.set_text(data.text);
            that.dirty = true;
        });

	$([IPython.events]).on('set_dirty.Worksheet', function (event, data) {
            that.dirty = data.value;
        });

        $([IPython.events]).on('select.Cell', function (event, data) {
            var index = that.find_cell_index(data.cell);
            that.select(index);
        });

    };


    Worksheet.prototype.scroll_to_bottom = function () {
        this.element.animate({scrollTop:this.element.get(0).scrollHeight}, 0);
    };


    Worksheet.prototype.scroll_to_top = function () {
        this.element.animate({scrollTop:0}, 0);
    };

    // Cell indexing, retrieval, etc.

    Worksheet.prototype.get_cell_elements = function () {
        return this.element.children("div.cell");
    };


    Worksheet.prototype.get_cell_element = function (index) {
        var result = null;
        var e = this.get_cell_elements().eq(index);
        if (e.length !== 0) {
            result = e;
        }
        return result;
    };


    Worksheet.prototype.ncells = function () {
        return this.get_cell_elements().length;
    };


    // TODO: we are often calling cells as cells()[i], which we should optimize
    // to cells(i) or a new method.
    Worksheet.prototype.get_cells = function () {
        return this.get_cell_elements().toArray().map(function (e) {
            return $(e).data("cell");
        });
    };


    Worksheet.prototype.get_cell = function (index) {
        var result = null;
        var ce = this.get_cell_element(index);
        if (ce !== null) {
            result = ce.data('cell');
        }
        return result;
    }


    Worksheet.prototype.get_next_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index < this.ncells()) {
            result = this.get_cell(index+1);
        }
        return result;
    }


    Worksheet.prototype.get_prev_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index > 1) {
            result = this.get_cell(index-1);
        }
        return result;
    }

    Worksheet.prototype.find_cell_index = function (cell) {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell") === cell) {
                result = index;
            };
        });
        return result;
    };


    Worksheet.prototype.index_or_selected = function (index) {
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


    Worksheet.prototype.get_selected_cell = function () {
        var index = this.get_selected_index();
        return this.get_cell(index);
    };


    Worksheet.prototype.is_valid_cell_index = function (index) {
        if (index !== null && index >= 0 && index < this.ncells()) {
            return true;
        } else {
            return false;
        };
    }

    Worksheet.prototype.get_selected_index = function () {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell").selected === true) {
                result = index;
            };
        });
        return result;
    };


    // Cell selection.

    Worksheet.prototype.select = function (index) {
        if (index !== undefined && index >= 0 && index < this.ncells()) {
            sindex = this.get_selected_index()
            if (sindex !== null && index !== sindex) {
                this.get_cell(sindex).unselect();
            };
            var cell = this.get_cell(index)
            cell.select();
            if (cell.cell_type === 'heading') {
                $([IPython.events]).trigger('selected_cell_type_changed.Worksheet',
                    {'cell_type':cell.cell_type,level:cell.level}
                );
            } else {
                $([IPython.events]).trigger('selected_cell_type_changed.Worksheet',
                    {'cell_type':cell.cell_type}
                );
            };
        };
        return this;
    };


    Worksheet.prototype.select_next = function () {
        var index = this.get_selected_index();
        if (index !== null && index >= 0 && (index+1) < this.ncells()) {
            this.select(index+1);
        };
        return this;
    };


    Worksheet.prototype.select_prev = function () {
        var index = this.get_selected_index();
        if (index !== null && index >= 0 && (index-1) < this.ncells()) {
            this.select(index-1);
        };
        return this;
    };


    // Cell movement

    Worksheet.prototype.move_cell_up = function (index) {
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


    Worksheet.prototype.move_cell_down = function (index) {
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


    Worksheet.prototype.sort_cells = function () {
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

    Worksheet.prototype.delete_cell = function (index) {
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


    Worksheet.prototype.insert_cell_below = function (type, index) {
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


    Worksheet.prototype.insert_cell_above = function (type, index) {
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


    Worksheet.prototype.to_code = function (index) {
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


    Worksheet.prototype.to_markdown = function (index) {
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


    Worksheet.prototype.to_html = function (index) {
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


    Worksheet.prototype.to_raw = function (index) {
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


    Worksheet.prototype.to_heading = function (index, level) {
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
            $([IPython.events]).trigger('selected_cell_type_changed.Worksheet',
                {'cell_type':'heading',level:level}
            );
        };
    };


    // Cut/Copy/Paste

    Worksheet.prototype.enable_paste = function () {
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


    Worksheet.prototype.disable_paste = function () {
        if (this.paste_enabled) {
            $('#paste_cell').addClass('ui-state-disabled').off('click');
            $('#paste_cell_above').addClass('ui-state-disabled').off('click');
            $('#paste_cell_below').addClass('ui-state-disabled').off('click');
            this.paste_enabled = false;
        };
    };


    Worksheet.prototype.cut_cell = function () {
        this.copy_cell();
        this.delete_cell();
    }

    Worksheet.prototype.copy_cell = function () {
        var cell = this.get_selected_cell();
        this.clipboard = cell.toJSON();
        this.enable_paste();
    };


    Worksheet.prototype.paste_cell = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            old_cell = this.get_next_cell(new_cell);
            this.delete_cell(this.find_cell_index(old_cell));
            this.select(this.find_cell_index(new_cell));
        };
    };


    Worksheet.prototype.paste_cell_above = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };


    Worksheet.prototype.paste_cell_below = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_below(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };


    // Split/merge

    Worksheet.prototype.split_cell = function () {
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


    Worksheet.prototype.merge_cell_above = function () {
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


    Worksheet.prototype.merge_cell_below = function () {
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

    Worksheet.prototype.collapse = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).collapse();
        this.dirty = true;
    };


    Worksheet.prototype.expand = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).expand();
        this.dirty = true;
    };


    Worksheet.prototype.toggle_output = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output();
        this.dirty = true;
    };


    Worksheet.prototype.toggle_output_scroll = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output_scroll();
    };


    Worksheet.prototype.collapse_all_output = function () {
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


    Worksheet.prototype.scroll_all_output = function () {
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


    Worksheet.prototype.expand_all_output = function () {
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


    Worksheet.prototype.clear_all_output = function () {
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

    Worksheet.prototype.cell_toggle_line_numbers = function() {
        this.get_selected_cell().toggle_line_numbers();
    };


    // Refresh code mirror for all cells in worksheet
    Worksheet.prototype.refresh_code_mirror = function() {
	var cells = this.get_cells();
	for (var i=0; i<cells.length; i++) {
	    cells[i].refresh();
	}
    }


    // Kernel related things

    Worksheet.prototype.set_kernel = function (kernel) {
	this.kernel = kernel;
	// Now that the kernel has been created, tell the CodeCells about it.
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            var cell = this.get_cell(i);
            if (cell instanceof IPython.CodeCell) {
                cell.set_kernel(this.kernel)
            };
        };
    }

    Worksheet.prototype.execute_selected_cell = function (options) {
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


    Worksheet.prototype.execute_all_cells = function () {
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            this.select(i);
            this.execute_selected_cell({add_new:false});
        };
        this.scroll_to_bottom();
    };

    // Persistance and loading

    Worksheet.prototype.get_worksheet_id = function () {
	return this.worksheet_id;
    };

    Worksheet.prototype.get_worksheet_name = function () {
	return this.metadata.name;
    };

    Worksheet.prototype.set_worksheet_name = function (name) {
	this.metadata.name = name;
    }


    Worksheet.prototype.fromJSON = function (data) {
        var ncells = this.ncells();
        var i;
        for (i=0; i<ncells; i++) {
            // Always delete cell 0 as they get renumbered as they are deleted.
            this.delete_cell(0);
        };
        // Save the metadata and name.
        if(data.metadata !== undefined) {
	    this.metadata = data.metadata;
	}
        var new_cells = data.cells;
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


    Worksheet.prototype.toJSON = function () {
        var cells = this.get_cells();
        var ncells = cells.length;
        var cell_array = new Array(ncells);
        for (var i=0; i<ncells; i++) {
            cell_array[i] = cells[i].toJSON();
        };
        var data = {
            cells: cell_array,
            metadata: this.metadata
        };
        return data;
    };
    
    IPython.Worksheet = Worksheet;


    return IPython;

}(IPython));

