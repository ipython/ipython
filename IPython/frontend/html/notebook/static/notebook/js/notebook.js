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

    /**
     * A notebook contains and manages cells.
     * 
     * @class Notebook
     * @constructor
     * @param {String} selector A jQuery selector for the notebook's DOM element
     * @param {Object} [options] A config object
     */
    var Notebook = function (selector, options) {
        var options = options || {};
        this._baseProjectUrl = options.baseProjectUrl;
        this.read_only = options.read_only || IPython.read_only;

        this.element = $(selector);
        this.element.scroll();
        this.element.data("notebook", this);
        this.next_prompt_number = 1;
        this.kernel = null;
        this.clipboard = null;
        this.undelete_backup = null;
        this.undelete_index = null;
        this.undelete_below = false;
        this.paste_enabled = false;
        this.set_dirty(false);
        this.metadata = {};
        this._checkpoint_after_save = false;
        this.last_checkpoint = null;
        this.autosave_interval = 0;
        this.autosave_timer = null;
        // autosave *at most* every two minutes
        this.minimum_autosave_interval = 120000;
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

    /**
     * Tweak the notebook's CSS style.
     * 
     * @method style
     */
    Notebook.prototype.style = function () {
        $('div#notebook').addClass('border-box-sizing');
    };

    /**
     * Get the root URL of the notebook server.
     * 
     * @method baseProjectUrl
     * @return {String} The base project URL
     */
    Notebook.prototype.baseProjectUrl = function(){
        return this._baseProjectUrl || $('body').data('baseProjectUrl');
    };

    /**
     * Create an HTML and CSS representation of the notebook.
     * 
     * @method create_elements
     */
    Notebook.prototype.create_elements = function () {
        // We add this end_space div to the end of the notebook div to:
        // i) provide a margin between the last cell and the end of the notebook
        // ii) to prevent the div from scrolling up when the last cell is being
        // edited, but is too low on the page, which browsers will do automatically.
        var that = this;
        this.container = $("<div/>").addClass("container").attr("id", "notebook-container");
        var end_space = $('<div/>').addClass('end_space').height("30%");
        end_space.dblclick(function (e) {
            if (that.read_only) return;
            var ncells = that.ncells();
            that.insert_cell_below('code',ncells-1);
        });
        this.element.append(this.container);
        this.container.append(end_space);
        $('div#notebook').addClass('border-box-sizing');
    };

    /**
     * Bind JavaScript events: key presses and custom IPython events.
     * 
     * @method bind_events
     */
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
                that.save_checkpoint();
                event.preventDefault();
                return false;
            } else if (event.which === key.ESC) {
                // Intercept escape at highest level to avoid closing
                // websocket connection with firefox
                IPython.pager.collapse();
                event.preventDefault();
            } else if (event.which === key.SHIFT) {
                // ignore shift keydown
                return true;
            }
            if (event.which === key.UPARROW && !event.shiftKey) {
                var cell = that.get_selected_cell();
                if (cell && cell.at_top()) {
                    event.preventDefault();
                    that.select_prev();
                };
            } else if (event.which === key.DOWNARROW && !event.shiftKey) {
                var cell = that.get_selected_cell();
                if (cell && cell.at_bottom()) {
                    event.preventDefault();
                    that.select_next();
                };
            } else if (event.which === key.ENTER && event.shiftKey) {
                that.execute_selected_cell();
                return false;
            } else if (event.which === key.ENTER && event.altKey) {
                // Execute code cell, and insert new in place
                that.execute_selected_cell();
                 // Only insert a new cell, if we ended up in an already populated cell
                if (/\S/.test(that.get_selected_cell().get_text()) == true) {
                    that.insert_cell_above('code');
                }
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
                // Paste below selected cell = v
                that.paste_cell_below();
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
                that.save_checkpoint();
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
            } else if (event.which === 90 && that.control_key_active) {
                // Undo last cell delete = z
                that.undelete();
                that.control_key_active = false;
                return false;
            } else if (that.control_key_active) {
                that.control_key_active = false;
                return true;
            }
            return true;
        });
        
        var collapse_time = function(time){
            var app_height = $('#ipython-main-app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var new_height = app_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, time);
        }

        this.element.bind('collapse_pager', function (event,extrap) {
            var time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            collapse_time(time);
        });

        var expand_time = function(time) {
            var app_height = $('#ipython-main-app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var pager_height = $('div#pager').outerHeight(true);
            var new_height = app_height - pager_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, time);
        }

        this.element.bind('expand_pager', function (event, extrap) {
            var time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            expand_time(time);
        });

        $(window).bind('beforeunload', function () {
            // TODO: Make killing the kernel configurable.
            var kill_kernel = false;
            if (kill_kernel) {
                that.kernel.kill();
            }
            // if we are autosaving, trigger an autosave on nav-away
            if (that.dirty && that.autosave_interval && ! that.read_only) {
                that.save_notebook();
            };
            // Null is the *only* return value that will make the browser not
            // pop up the "don't leave" dialog.
            return null;
        });
    };

    /**
     * Set the dirty flag, and trigger the set_dirty.Notebook event
     * 
     * @method set_dirty
     */
    Notebook.prototype.set_dirty = function (value) {
        if (value === undefined) {
            value = true;
        }
        if (this.dirty == value) {
            return;
        }
        $([IPython.events]).trigger('set_dirty.Notebook', {value: value});
    };

    /**
     * Scroll the top of the page to a given cell.
     * 
     * @method scroll_to_cell
     * @param {Number} cell_number An index of the cell to view
     * @param {Number} time Animation time in milliseconds
     * @return {Number} Pixel offset from the top of the container
     */
    Notebook.prototype.scroll_to_cell = function (cell_number, time) {
        var cells = this.get_cells();
        var time = time || 0;
        cell_number = Math.min(cells.length-1,cell_number);
        cell_number = Math.max(0             ,cell_number);
        var scroll_value = cells[cell_number].element.position().top-cells[0].element.position().top ;
        this.element.animate({scrollTop:scroll_value}, time);
        return scroll_value;
    };

    /**
     * Scroll to the bottom of the page.
     * 
     * @method scroll_to_bottom
     */
    Notebook.prototype.scroll_to_bottom = function () {
        this.element.animate({scrollTop:this.element.get(0).scrollHeight}, 0);
    };

    /**
     * Scroll to the top of the page.
     * 
     * @method scroll_to_top
     */
    Notebook.prototype.scroll_to_top = function () {
        this.element.animate({scrollTop:0}, 0);
    };


    // Cell indexing, retrieval, etc.

    /**
     * Get all cell elements in the notebook.
     * 
     * @method get_cell_elements
     * @return {jQuery} A selector of all cell elements
     */
    Notebook.prototype.get_cell_elements = function () {
        return this.container.children("div.cell");
    };

    /**
     * Get a particular cell element.
     * 
     * @method get_cell_element
     * @param {Number} index An index of a cell to select
     * @return {jQuery} A selector of the given cell.
     */
    Notebook.prototype.get_cell_element = function (index) {
        var result = null;
        var e = this.get_cell_elements().eq(index);
        if (e.length !== 0) {
            result = e;
        }
        return result;
    };

    /**
     * Count the cells in this notebook.
     * 
     * @method ncells
     * @return {Number} The number of cells in this notebook
     */
    Notebook.prototype.ncells = function () {
        return this.get_cell_elements().length;
    };

    /**
     * Get all Cell objects in this notebook.
     * 
     * @method get_cells
     * @return {Array} This notebook's Cell objects
     */
    // TODO: we are often calling cells as cells()[i], which we should optimize
    // to cells(i) or a new method.
    Notebook.prototype.get_cells = function () {
        return this.get_cell_elements().toArray().map(function (e) {
            return $(e).data("cell");
        });
    };

    /**
     * Get a Cell object from this notebook.
     * 
     * @method get_cell
     * @param {Number} index An index of a cell to retrieve
     * @return {Cell} A particular cell
     */
    Notebook.prototype.get_cell = function (index) {
        var result = null;
        var ce = this.get_cell_element(index);
        if (ce !== null) {
            result = ce.data('cell');
        }
        return result;
    }

    /**
     * Get the cell below a given cell.
     * 
     * @method get_next_cell
     * @param {Cell} cell The provided cell
     * @return {Cell} The next cell
     */
    Notebook.prototype.get_next_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (this.is_valid_cell_index(index+1)) {
            result = this.get_cell(index+1);
        }
        return result;
    }

    /**
     * Get the cell above a given cell.
     * 
     * @method get_prev_cell
     * @param {Cell} cell The provided cell
     * @return {Cell} The previous cell
     */
    Notebook.prototype.get_prev_cell = function (cell) {
        // TODO: off-by-one
        // nb.get_prev_cell(nb.get_cell(1)) is null
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index > 1) {
            result = this.get_cell(index-1);
        }
        return result;
    }
    
    /**
     * Get the numeric index of a given cell.
     * 
     * @method find_cell_index
     * @param {Cell} cell The provided cell
     * @return {Number} The cell's numeric index
     */
    Notebook.prototype.find_cell_index = function (cell) {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell") === cell) {
                result = index;
            };
        });
        return result;
    };

    /**
     * Get a given index , or the selected index if none is provided.
     * 
     * @method index_or_selected
     * @param {Number} index A cell's index
     * @return {Number} The given index, or selected index if none is provided.
     */
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

    /**
     * Get the currently selected cell.
     * @method get_selected_cell
     * @return {Cell} The selected cell
     */
    Notebook.prototype.get_selected_cell = function () {
        var index = this.get_selected_index();
        return this.get_cell(index);
    };

    /**
     * Check whether a cell index is valid.
     * 
     * @method is_valid_cell_index
     * @param {Number} index A cell index
     * @return True if the index is valid, false otherwise
     */
    Notebook.prototype.is_valid_cell_index = function (index) {
        if (index !== null && index >= 0 && index < this.ncells()) {
            return true;
        } else {
            return false;
        };
    }

    /**
     * Get the index of the currently selected cell.
     
     * @method get_selected_index
     * @return {Number} The selected cell's numeric index
     */
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

    /**
     * Programmatically select a cell.
     * 
     * @method select
     * @param {Number} index A cell's index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.select = function (index) {
        if (this.is_valid_cell_index(index)) {
            var sindex = this.get_selected_index()
            if (sindex !== null && index !== sindex) {
                this.get_cell(sindex).unselect();
            };
            var cell = this.get_cell(index);
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

    /**
     * Programmatically select the next cell.
     *
     * @method select_next
     * @return {Notebook} This notebook
     */
    Notebook.prototype.select_next = function () {
        var index = this.get_selected_index();
        this.select(index+1);
        return this;
    };

    /**
     * Programmatically select the previous cell.
     *
     * @method select_prev
     * @return {Notebook} This notebook
     */
    Notebook.prototype.select_prev = function () {
        var index = this.get_selected_index();
        this.select(index-1);
        return this;
    };


    // Cell movement

    /**
     * Move given (or selected) cell up and select it.
     * 
     * @method move_cell_up
     * @param [index] {integer} cell index
     * @return {Notebook} This notebook
     **/
    Notebook.prototype.move_cell_up = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i) && i > 0) {
            var pivot = this.get_cell_element(i-1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.before(tomove);
                this.select(i-1);
            };
            this.set_dirty(true);
        };
        return this;
    };


    /**
     * Move given (or selected) cell down and select it
     * 
     * @method move_cell_down
     * @param [index] {integer} cell index
     * @return {Notebook} This notebook
     **/
    Notebook.prototype.move_cell_down = function (index) {
        var i = this.index_or_selected(index);
        if ( this.is_valid_cell_index(i) && this.is_valid_cell_index(i+1)) {
            var pivot = this.get_cell_element(i+1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.after(tomove);
                this.select(i+1);
            };
        };
        this.set_dirty();
        return this;
    };


    // Insertion, deletion.

    /**
     * Delete a cell from the notebook.
     * 
     * @method delete_cell
     * @param [index] A cell's numeric index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.delete_cell = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_selected_cell();
        this.undelete_backup = cell.toJSON();
        $('#undelete_cell').removeClass('ui-state-disabled');
        if (this.is_valid_cell_index(i)) {
            var ce = this.get_cell_element(i);
            ce.remove();
            if (i === (this.ncells())) {
                this.select(i-1);
                this.undelete_index = i - 1;
                this.undelete_below = true;
            } else {
                this.select(i);
                this.undelete_index = i;
                this.undelete_below = false;
            };
            this.set_dirty(true);
        };
        return this;
    };

    /**
     * Insert a cell so that after insertion the cell is at given index.
     *
     * Similar to insert_above, but index parameter is mandatory
     *
     * Index will be brought back into the accissible range [0,n]
     *
     * @method insert_cell_at_index
     * @param type {string} in ['code','markdown','heading']
     * @param [index] {int} a valid index where to inser cell
     *
     * @return cell {cell|null} created cell or null
     **/
    Notebook.prototype.insert_cell_at_index = function(type, index){

        var ncells = this.ncells();
        var index = Math.min(index,ncells);
            index = Math.max(index,0);
        var cell = null;

        if (ncells === 0 || this.is_valid_cell_index(index) || index === ncells) {
            if (type === 'code') {
                cell = new IPython.CodeCell(this.kernel);
                cell.set_input_prompt();
            } else if (type === 'markdown') {
                cell = new IPython.MarkdownCell();
            } else if (type === 'raw') {
                cell = new IPython.RawCell();
            } else if (type === 'heading') {
                cell = new IPython.HeadingCell();
            }

            if(this._insert_element_at_index(cell.element,index)){
                cell.render();
                this.select(this.find_cell_index(cell));
                this.set_dirty(true);
            }
        }
        return cell;

    };

    /**
     * Insert an element at given cell index.
     *
     * @method _insert_element_at_index
     * @param element {dom element} a cell element
     * @param [index] {int} a valid index where to inser cell
     * @private
     *
     * return true if everything whent fine.
     **/
    Notebook.prototype._insert_element_at_index = function(element, index){
        if (element === undefined){
            return false;
        }

        var ncells = this.ncells();

        if (ncells === 0) {
            // special case append if empty
            this.element.find('div.end_space').before(element);
        } else if ( ncells === index ) {
            // special case append it the end, but not empty
            this.get_cell_element(index-1).after(element);
        } else if (this.is_valid_cell_index(index)) {
            // otherwise always somewhere to append to
            this.get_cell_element(index).before(element);
        } else {
            return false;
        }

        if (this.undelete_index !== null && index <= this.undelete_index) {
            this.undelete_index = this.undelete_index + 1;
            this.set_dirty(true);
        }
        return true;
    };

    /**
     * Insert a cell of given type above given index, or at top
     * of notebook if index smaller than 0.
     *
     * default index value is the one of currently selected cell
     *
     * @method insert_cell_above
     * @param type {string} cell type
     * @param [index] {integer}
     *
     * @return handle to created cell or null
     **/
    Notebook.prototype.insert_cell_above = function (type, index) {
        index = this.index_or_selected(index);
        return this.insert_cell_at_index(type, index);
    };

    /**
     * Insert a cell of given type below given index, or at bottom
     * of notebook if index greater thatn number of cell
     *
     * default index value is the one of currently selected cell
     *
     * @method insert_cell_below
     * @param type {string} cell type
     * @param [index] {integer}
     *
     * @return handle to created cell or null
     *
     **/
    Notebook.prototype.insert_cell_below = function (type, index) {
        index = this.index_or_selected(index);
        return this.insert_cell_at_index(type, index+1);
    };


    /**
     * Insert cell at end of notebook
     *
     * @method insert_cell_at_bottom
     * @param {String} type cell type
     *
     * @return the added cell; or null
     **/
    Notebook.prototype.insert_cell_at_bottom = function (type){
        var len = this.ncells();
        return this.insert_cell_below(type,len-1);
    };

    /**
     * Turn a cell into a code cell.
     * 
     * @method to_code
     * @param {Number} [index] A cell's index
     */
    Notebook.prototype.to_code = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            if (!(source_cell instanceof IPython.CodeCell)) {
                var target_cell = this.insert_cell_below('code',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                }
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_element.remove();
                this.set_dirty(true);
            };
        };
    };

    /**
     * Turn a cell into a Markdown cell.
     * 
     * @method to_markdown
     * @param {Number} [index] A cell's index
     */
    Notebook.prototype.to_markdown = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_element = this.get_cell_element(i);
            var source_cell = source_element.data("cell");
            if (!(source_cell instanceof IPython.MarkdownCell)) {
                var target_cell = this.insert_cell_below('markdown',i);
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
                this.set_dirty(true);
            };
        };
    };

    /**
     * Turn a cell into a raw text cell.
     * 
     * @method to_raw
     * @param {Number} [index] A cell's index
     */
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
                this.set_dirty(true);
            };
        };
    };

    /**
     * Turn a cell into a heading cell.
     * 
     * @method to_heading
     * @param {Number} [index] A cell's index
     * @param {Number} [level] A heading level (e.g., 1 becomes &lt;h1&gt;)
     */
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
                this.set_dirty(true);
            };
            $([IPython.events]).trigger('selected_cell_type_changed.Notebook',
                {'cell_type':'heading',level:level}
            );
        };
    };


    // Cut/Copy/Paste

    /**
     * Enable UI elements for pasting cells.
     * 
     * @method enable_paste
     */
    Notebook.prototype.enable_paste = function () {
        var that = this;
        if (!this.paste_enabled) {
            $('#paste_cell_replace').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell_replace();});
            $('#paste_cell_above').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell_above();});
            $('#paste_cell_below').removeClass('ui-state-disabled')
                .on('click', function () {that.paste_cell_below();});
            this.paste_enabled = true;
        };
    };

    /**
     * Disable UI elements for pasting cells.
     * 
     * @method disable_paste
     */
    Notebook.prototype.disable_paste = function () {
        if (this.paste_enabled) {
            $('#paste_cell_replace').addClass('ui-state-disabled').off('click');
            $('#paste_cell_above').addClass('ui-state-disabled').off('click');
            $('#paste_cell_below').addClass('ui-state-disabled').off('click');
            this.paste_enabled = false;
        };
    };

    /**
     * Cut a cell.
     * 
     * @method cut_cell
     */
    Notebook.prototype.cut_cell = function () {
        this.copy_cell();
        this.delete_cell();
    }

    /**
     * Copy a cell.
     * 
     * @method copy_cell
     */
    Notebook.prototype.copy_cell = function () {
        var cell = this.get_selected_cell();
        this.clipboard = cell.toJSON();
        this.enable_paste();
    };

    /**
     * Replace the selected cell with a cell in the clipboard.
     * 
     * @method paste_cell_replace
     */
    Notebook.prototype.paste_cell_replace = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            var old_cell = this.get_next_cell(new_cell);
            this.delete_cell(this.find_cell_index(old_cell));
            this.select(this.find_cell_index(new_cell));
        };
    };

    /**
     * Paste a cell from the clipboard above the selected cell.
     * 
     * @method paste_cell_above
     */
    Notebook.prototype.paste_cell_above = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };

    /**
     * Paste a cell from the clipboard below the selected cell.
     * 
     * @method paste_cell_below
     */
    Notebook.prototype.paste_cell_below = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_below(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
        };
    };

    // Cell undelete

    /**
     * Restore the most recently deleted cell.
     * 
     * @method undelete
     */
    Notebook.prototype.undelete = function() {
        if (this.undelete_backup !== null && this.undelete_index !== null) {
            var current_index = this.get_selected_index();
            if (this.undelete_index < current_index) {
                current_index = current_index + 1;
            }
            if (this.undelete_index >= this.ncells()) {
                this.select(this.ncells() - 1);
            }
            else {
                this.select(this.undelete_index);
            }
            var cell_data = this.undelete_backup;
            var new_cell = null;
            if (this.undelete_below) {
                new_cell = this.insert_cell_below(cell_data.cell_type);
            } else {
                new_cell = this.insert_cell_above(cell_data.cell_type);
            }
            new_cell.fromJSON(cell_data);
            this.select(current_index);
            this.undelete_backup = null;
            this.undelete_index = null;
        }
        $('#undelete_cell').addClass('ui-state-disabled');
    }

    // Split/merge

    /**
     * Split the selected cell into two, at the cursor.
     * 
     * @method split_cell
     */
    Notebook.prototype.split_cell = function () {
        // Todo: implement spliting for other cell types.
        var cell = this.get_selected_cell();
        if (cell.is_splittable()) {
            var texta = cell.get_pre_cursor();
            var textb = cell.get_post_cursor();
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
            }
        };
    };

    /**
     * Combine the selected cell into the cell above it.
     * 
     * @method merge_cell_above
     */
    Notebook.prototype.merge_cell_above = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        if (index > 0) {
            var upper_cell = this.get_cell(index-1);
            var upper_text = upper_cell.get_text();
            var text = cell.get_text();
            if (cell instanceof IPython.CodeCell) {
                cell.set_text(upper_text+'\n'+text);
            } else if (cell instanceof IPython.MarkdownCell) {
                cell.edit();
                cell.set_text(upper_text+'\n'+text);
                cell.render();
            };
            this.delete_cell(index-1);
            this.select(this.find_cell_index(cell));
        };
    };

    /**
     * Combine the selected cell into the cell below it.
     * 
     * @method merge_cell_below
     */
    Notebook.prototype.merge_cell_below = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        if (index < this.ncells()-1) {
            var lower_cell = this.get_cell(index+1);
            var lower_text = lower_cell.get_text();
            var text = cell.get_text();
            if (cell instanceof IPython.CodeCell) {
                cell.set_text(text+'\n'+lower_text);
            } else if (cell instanceof IPython.MarkdownCell) {
                cell.edit();
                cell.set_text(text+'\n'+lower_text);
                cell.render();
            };
            this.delete_cell(index+1);
            this.select(this.find_cell_index(cell));
        };
    };


    // Cell collapsing and output clearing

    /**
     * Hide a cell's output.
     * 
     * @method collapse
     * @param {Number} index A cell's numeric index
     */
    Notebook.prototype.collapse = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).collapse();
        this.set_dirty(true);
    };

    /**
     * Show a cell's output.
     * 
     * @method expand
     * @param {Number} index A cell's numeric index
     */
    Notebook.prototype.expand = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).expand();
        this.set_dirty(true);
    };

    /** Toggle whether a cell's output is collapsed or expanded.
     * 
     * @method toggle_output
     * @param {Number} index A cell's numeric index
     */
    Notebook.prototype.toggle_output = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output();
        this.set_dirty(true);
    };

    /**
     * Toggle a scrollbar for long cell outputs.
     * 
     * @method toggle_output_scroll
     * @param {Number} index A cell's numeric index
     */
    Notebook.prototype.toggle_output_scroll = function (index) {
        var i = this.index_or_selected(index);
        this.get_cell(i).toggle_output_scroll();
    };

    /**
     * Hide each code cell's output area.
     * 
     * @method collapse_all_output
     */
    Notebook.prototype.collapse_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].output_area.collapse();
            }
        };
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /**
     * Expand each code cell's output area, and add a scrollbar for long output.
     * 
     * @method scroll_all_output
     */
    Notebook.prototype.scroll_all_output = function () {
        var ncells = this.ncells();
        var cells = this.get_cells();
        for (var i=0; i<ncells; i++) {
            if (cells[i] instanceof IPython.CodeCell) {
                cells[i].output_area.expand();
                cells[i].output_area.scroll_if_long();
            }
        };
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /**
     * Expand each code cell's output area, and remove scrollbars.
     * 
     * @method expand_all_output
     */
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
        this.set_dirty(true);
    };

    /**
     * Clear each code cell's output area.
     * 
     * @method clear_all_output
     */
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
        this.set_dirty(true);
    };


    // Other cell functions: line numbers, ...

    /**
     * Toggle line numbers in the selected cell's input area.
     * 
     * @method cell_toggle_line_numbers
     */
    Notebook.prototype.cell_toggle_line_numbers = function() {
        this.get_selected_cell().toggle_line_numbers();
    };

    // Kernel related things

    /**
     * Start a new kernel and set it on each code cell.
     * 
     * @method start_kernel
     */
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

    /**
     * Prompt the user to restart the IPython kernel.
     * 
     * @method restart_kernel
     */
    Notebook.prototype.restart_kernel = function () {
        var that = this;
        IPython.dialog.modal({
            title : "Restart kernel or continue running?",
            body : $("<p/>").html(
                'Do you want to restart the current kernel?  You will lose all variables defined in it.'
            ),
            buttons : {
                "Continue running" : {},
                "Restart" : {
                    "class" : "btn-danger",
                    "click" : function() {
                        that.kernel.restart();
                    }
                }
            }
        });
    };

    /**
     * Run the selected cell.
     * 
     * Execute or render cell outputs.
     * 
     * @method execute_selected_cell
     * @param {Object} options Customize post-execution behavior
     */
    Notebook.prototype.execute_selected_cell = function (options) {
        // add_new: should a new cell be added if we are at the end of the nb
        // terminal: execute in terminal mode, which stays in the current cell
        var default_options = {terminal: false, add_new: true};
        $.extend(default_options, options);
        var that = this;
        var cell = that.get_selected_cell();
        var cell_index = that.find_cell_index(cell);
        if (cell instanceof IPython.CodeCell) {
            cell.execute();
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
        this.set_dirty(true);
    };

    /**
     * Execute all cells below the selected cell.
     * 
     * @method execute_cells_below
     */
    Notebook.prototype.execute_cells_below = function () {
        this.execute_cell_range(this.get_selected_index(), this.ncells());
        this.scroll_to_bottom();
    };

    /**
     * Execute all cells above the selected cell.
     * 
     * @method execute_cells_above
     */
    Notebook.prototype.execute_cells_above = function () {
        this.execute_cell_range(0, this.get_selected_index());
    };

    /**
     * Execute all cells.
     * 
     * @method execute_all_cells
     */
    Notebook.prototype.execute_all_cells = function () {
        this.execute_cell_range(0, this.ncells());
        this.scroll_to_bottom();
    };

    /**
     * Execute a contiguous range of cells.
     * 
     * @method execute_cell_range
     * @param {Number} start Index of the first cell to execute (inclusive)
     * @param {Number} end Index of the last cell to execute (exclusive)
     */
    Notebook.prototype.execute_cell_range = function (start, end) {
        for (var i=start; i<end; i++) {
            this.select(i);
            this.execute_selected_cell({add_new:false});
        };
    };

    // Persistance and loading

    /**
     * Getter method for this notebook's ID.
     * 
     * @method get_notebook_id
     * @return {String} This notebook's ID
     */
    Notebook.prototype.get_notebook_id = function () {
        return this.notebook_id;
    };

    /**
     * Getter method for this notebook's name.
     * 
     * @method get_notebook_name
     * @return {String} This notebook's name
     */
    Notebook.prototype.get_notebook_name = function () {
        return this.notebook_name;
    };

    /**
     * Setter method for this notebook's name.
     *
     * @method set_notebook_name
     * @param {String} name A new name for this notebook
     */
    Notebook.prototype.set_notebook_name = function (name) {
        this.notebook_name = name;
    };

    /**
     * Check that a notebook's name is valid.
     * 
     * @method test_notebook_name
     * @param {String} nbname A name for this notebook
     * @return {Boolean} True if the name is valid, false if invalid
     */
    Notebook.prototype.test_notebook_name = function (nbname) {
        nbname = nbname || '';
        if (this.notebook_name_blacklist_re.test(nbname) == false && nbname.length>0) {
            return true;
        } else {
            return false;
        };
    };

    /**
     * Load a notebook from JSON (.ipynb).
     * 
     * This currently handles one worksheet: others are deleted.
     * 
     * @method fromJSON
     * @param {Object} data JSON representation of a notebook
     */
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
            IPython.dialog.modal({
                title : "Multiple worksheets",
                body : "This notebook has " + data.worksheets.length + " worksheets, " +
                    "but this version of IPython can only handle the first.  " +
                    "If you save this notebook, worksheets after the first will be lost.",
                buttons : {
                    OK : {
                        class : "btn-danger"
                    }
                }
            });
        }
    };

    /**
     * Dump this notebook into a JSON-friendly object.
     * 
     * @method toJSON
     * @return {Object} A JSON-friendly representation of this notebook.
     */
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

    /**
     * Start an autosave timer, for periodically saving the notebook.
     * 
     * @method set_autosave_interval
     * @param {Integer} interval the autosave interval in milliseconds
     */
    Notebook.prototype.set_autosave_interval = function (interval) {
        var that = this;
        // clear previous interval, so we don't get simultaneous timers
        if (this.autosave_timer) {
            clearInterval(this.autosave_timer);
        }
        
        this.autosave_interval = this.minimum_autosave_interval = interval;
        if (interval) {
            this.autosave_timer = setInterval(function() {
                if (that.dirty) {
                    that.save_notebook();
                }
            }, interval);
            $([IPython.events]).trigger("autosave_enabled.Notebook", interval);
        } else {
            this.autosave_timer = null;
            $([IPython.events]).trigger("autosave_disabled.Notebook");
        };
    };
    
    /**
     * Save this notebook on the server.
     * 
     * @method save_notebook
     */
    Notebook.prototype.save_notebook = function () {
        // We may want to move the name/id/nbformat logic inside toJSON?
        var data = this.toJSON();
        data.metadata.name = this.notebook_name;
        data.nbformat = this.nbformat;
        data.nbformat_minor = this.nbformat_minor;
        
        // time the ajax call for autosave tuning purposes.
        var start =  new Date().getTime();

        // We do the call with settings so we can set cache to false.
        var settings = {
            processData : false,
            cache : false,
            type : "PUT",
            data : JSON.stringify(data),
            headers : {'Content-Type': 'application/json'},
            success : $.proxy(this.save_notebook_success, this, start),
            error : $.proxy(this.save_notebook_error, this)
        };
        $([IPython.events]).trigger('notebook_saving.Notebook');
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id;
        $.ajax(url, settings);
    };
    
    /**
     * Success callback for saving a notebook.
     * 
     * @method save_notebook_success
     * @param {Integer} start the time when the save request started
     * @param {Object} data JSON representation of a notebook
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.save_notebook_success = function (start, data, status, xhr) {
        this.set_dirty(false);
        $([IPython.events]).trigger('notebook_saved.Notebook');
        this._update_autosave_interval(start);
        if (this._checkpoint_after_save) {
            this.create_checkpoint();
            this._checkpoint_after_save = false;
        };
    };
    
    /**
     * update the autosave interval based on how long the last save took
     * 
     * @method _update_autosave_interval
     * @param {Integer} timestamp when the save request started
     */
    Notebook.prototype._update_autosave_interval = function (start) {
        var duration = (new Date().getTime() - start);
        if (this.autosave_interval) {
            // new save interval: higher of 10x save duration or parameter (default 30 seconds)
            var interval = Math.max(10 * duration, this.minimum_autosave_interval);
            // round to 10 seconds, otherwise we will be setting a new interval too often
            interval = 10000 * Math.round(interval / 10000);
            // set new interval, if it's changed
            if (interval != this.autosave_interval) {
                this.set_autosave_interval(interval);
            }
        }
    };
    
    /**
     * Failure callback for saving a notebook.
     * 
     * @method save_notebook_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} status Description of response status
     * @param {String} error_msg HTTP error message
     */
    Notebook.prototype.save_notebook_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('notebook_save_failed.Notebook');
    };
    
    /**
     * Request a notebook's data from the server.
     * 
     * @method load_notebook
     * @param {String} notebook_id A notebook to load
     */
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
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id;
        $.ajax(url, settings);
    };

    /**
     * Success callback for loading a notebook from the server.
     * 
     * Load notebook data from the JSON response.
     * 
     * @method load_notebook_success
     * @param {Object} data JSON representation of a notebook
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.load_notebook_success = function (data, status, xhr) {
        this.fromJSON(data);
        if (this.ncells() === 0) {
            this.insert_cell_below('code');
        };
        this.set_dirty(false);
        this.select(0);
        this.scroll_to_top();
        if (data.orig_nbformat !== undefined && data.nbformat !== data.orig_nbformat) {
            var msg = "This notebook has been converted from an older " +
            "notebook format (v"+data.orig_nbformat+") to the current notebook " +
            "format (v"+data.nbformat+"). The next time you save this notebook, the " +
            "newer notebook format will be used and older versions of IPython " +
            "may not be able to read it. To keep the older version, close the " +
            "notebook without saving it.";
            IPython.dialog.modal({
                title : "Notebook converted",
                body : msg,
                buttons : {
                    OK : {
                        class : "btn-primary"
                    }
                }
            });
        } else if (data.orig_nbformat_minor !== undefined && data.nbformat_minor !== data.orig_nbformat_minor) {
            var that = this;
            var orig_vs = 'v' + data.nbformat + '.' + data.orig_nbformat_minor;
            var this_vs = 'v' + data.nbformat + '.' + this.nbformat_minor;
            var msg = "This notebook is version " + orig_vs + ", but we only fully support up to " +
            this_vs + ".  You can still work with this notebook, but some features " +
            "introduced in later notebook versions may not be available."

            IPython.dialog.modal({
                title : "Newer Notebook",
                body : msg,
                buttons : {
                    OK : {
                        class : "btn-danger"
                    }
                }
            });

        }
        
        // Create the kernel after the notebook is completely loaded to prevent
        // code execution upon loading, which is a security risk.
        if (! this.read_only) {
            this.start_kernel();
            // load our checkpoint list
            IPython.notebook.list_checkpoints();
        }
        $([IPython.events]).trigger('notebook_loaded.Notebook');
    };

    /**
     * Failure callback for loading a notebook from the server.
     * 
     * @method load_notebook_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} textStatus Description of response status
     * @param {String} errorThrow HTTP error message
     */
    Notebook.prototype.load_notebook_error = function (xhr, textStatus, errorThrow) {
        if (xhr.status === 500) {
            var msg = "An error occurred while loading this notebook. Most likely " +
            "this notebook is in a newer format than is supported by this " +
            "version of IPython. This version can load notebook formats " +
            "v"+this.nbformat+" or earlier.";
            
            IPython.dialog.modal({
                title: "Error loading notebook",
                body : msg,
                buttons : {
                    "OK": {}
                }
            });
        }
    }

    /*********************  checkpoint-related  *********************/
    
    /**
     * Save the notebook then immediately create a checkpoint.
     * 
     * @method save_checkpoint
     */
    Notebook.prototype.save_checkpoint = function () {
        this._checkpoint_after_save = true;
        this.save_notebook();
    };
    
    /**
     * List checkpoints for this notebook.
     * 
     * @method list_checkpoint
     */
    Notebook.prototype.list_checkpoints = function () {
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id + '/checkpoints';
        $.get(url).done(
            $.proxy(this.list_checkpoints_success, this)
        ).fail(
            $.proxy(this.list_checkpoints_error, this)
        );
    };

    /**
     * Success callback for listing checkpoints.
     * 
     * @method list_checkpoint_success
     * @param {Object} data JSON representation of a checkpoint
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.list_checkpoints_success = function (data, status, xhr) {
        var data = $.parseJSON(data);
        if (data.length) {
            this.last_checkpoint = data[0];
        } else {
            this.last_checkpoint = null;
        }
        $([IPython.events]).trigger('checkpoints_listed.Notebook', [data]);
    };

    /**
     * Failure callback for listing a checkpoint.
     * 
     * @method list_checkpoint_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} status Description of response status
     * @param {String} error_msg HTTP error message
     */
    Notebook.prototype.list_checkpoints_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('list_checkpoints_failed.Notebook');
    };
    
    /**
     * Create a checkpoint of this notebook on the server from the most recent save.
     * 
     * @method create_checkpoint
     */
    Notebook.prototype.create_checkpoint = function () {
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id + '/checkpoints';
        $.post(url).done(
            $.proxy(this.create_checkpoint_success, this)
        ).fail(
            $.proxy(this.create_checkpoint_error, this)
        );
    };

    /**
     * Success callback for creating a checkpoint.
     * 
     * @method create_checkpoint_success
     * @param {Object} data JSON representation of a checkpoint
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.create_checkpoint_success = function (data, status, xhr) {
        var data = $.parseJSON(data);
        this.last_checkpoint = data;
        $([IPython.events]).trigger('checkpoint_created.Notebook', data);
    };

    /**
     * Failure callback for creating a checkpoint.
     * 
     * @method create_checkpoint_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} status Description of response status
     * @param {String} error_msg HTTP error message
     */
    Notebook.prototype.create_checkpoint_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('checkpoint_failed.Notebook');
    };
    
    Notebook.prototype.restore_checkpoint_dialog = function (checkpoint) {
        var that = this;
        var checkpoint = checkpoint || this.last_checkpoint;
        if ( ! checkpoint ) {
            console.log("restore dialog, but no checkpoint to restore to!");
            return;
        }
        var body = $('<div/>').append(
            $('<p/>').addClass("p-space").text(
                "Are you sure you want to revert the notebook to " +
                "the latest checkpoint?"
            ).append(
                $("<strong/>").text(
                    " This cannot be undone."
                )
            )
        ).append(
            $('<p/>').addClass("p-space").text("The checkpoint was last updated at:")
        ).append(
            $('<p/>').addClass("p-space").text(
                Date(checkpoint.last_modified)
            ).css("text-align", "center")
        );
        
        IPython.dialog.modal({
            title : "Revert notebook to checkpoint",
            body : body,
            buttons : {
                Revert : {
                    class : "btn-danger",
                    click : function () {
                        that.restore_checkpoint(checkpoint.checkpoint_id);
                    }
                },
                Cancel : {}
                }
        });
    }
    
    /**
     * Restore the notebook to a checkpoint state.
     * 
     * @method restore_checkpoint
     * @param {String} checkpoint ID
     */
    Notebook.prototype.restore_checkpoint = function (checkpoint) {
        $([IPython.events]).trigger('notebook_restoring.Notebook', checkpoint);
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id + '/checkpoints/' + checkpoint;
        $.post(url).done(
            $.proxy(this.restore_checkpoint_success, this)
        ).fail(
            $.proxy(this.restore_checkpoint_error, this)
        );
    };
    
    /**
     * Success callback for restoring a notebook to a checkpoint.
     * 
     * @method restore_checkpoint_success
     * @param {Object} data (ignored, should be empty)
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.restore_checkpoint_success = function (data, status, xhr) {
        $([IPython.events]).trigger('checkpoint_restored.Notebook');
        this.load_notebook(this.notebook_id);
    };

    /**
     * Failure callback for restoring a notebook to a checkpoint.
     * 
     * @method restore_checkpoint_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} status Description of response status
     * @param {String} error_msg HTTP error message
     */
    Notebook.prototype.restore_checkpoint_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('checkpoint_restore_failed.Notebook');
    };
    
    /**
     * Delete a notebook checkpoint.
     * 
     * @method delete_checkpoint
     * @param {String} checkpoint ID
     */
    Notebook.prototype.delete_checkpoint = function (checkpoint) {
        $([IPython.events]).trigger('notebook_restoring.Notebook', checkpoint);
        var url = this.baseProjectUrl() + 'notebooks/' + this.notebook_id + '/checkpoints/' + checkpoint;
        $.ajax(url, {
            type: 'DELETE',
            success: $.proxy(this.delete_checkpoint_success, this),
            error: $.proxy(this.delete_notebook_error,this)
        });
    };
    
    /**
     * Success callback for deleting a notebook checkpoint
     * 
     * @method delete_checkpoint_success
     * @param {Object} data (ignored, should be empty)
     * @param {String} status Description of response status
     * @param {jqXHR} xhr jQuery Ajax object
     */
    Notebook.prototype.delete_checkpoint_success = function (data, status, xhr) {
        $([IPython.events]).trigger('checkpoint_deleted.Notebook', data);
        this.load_notebook(this.notebook_id);
    };

    /**
     * Failure callback for deleting a notebook checkpoint.
     * 
     * @method delete_checkpoint_error
     * @param {jqXHR} xhr jQuery Ajax object
     * @param {String} status Description of response status
     * @param {String} error_msg HTTP error message
     */
    Notebook.prototype.delete_checkpoint_error = function (xhr, status, error_msg) {
        $([IPython.events]).trigger('checkpoint_delete_failed.Notebook');
    };


    IPython.Notebook = Notebook;


    return IPython;

}(IPython));

