// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

/**
 * @module notebook
 */
define(function (require) {
    "use strict";
    var IPython = require('base/js/namespace');
    var $ = require('jquery');
    var utils = require('base/js/utils');
    var dialog = require('base/js/dialog');
    var cellmod = require('notebook/js/cell');
    var textcell = require('notebook/js/textcell');
    var codecell = require('notebook/js/codecell');
    var moment = require('moment');
    var configmod = require('services/config');
    var session = require('services/sessions/session');
    var celltoolbar = require('notebook/js/celltoolbar');
    var marked = require('components/marked/lib/marked');
    var CodeMirror = require('codemirror/lib/codemirror');
    var runMode = require('codemirror/addon/runmode/runmode');
    var mathjaxutils = require('notebook/js/mathjaxutils');
    var keyboard = require('base/js/keyboard');
    var tooltip = require('notebook/js/tooltip');
    var default_celltoolbar = require('notebook/js/celltoolbarpresets/default');
    var rawcell_celltoolbar = require('notebook/js/celltoolbarpresets/rawcell');
    var slideshow_celltoolbar = require('notebook/js/celltoolbarpresets/slideshow');
    var scrollmanager = require('notebook/js/scrollmanager');

    /**
     * Contains and manages cells.
     * 
     * @class Notebook
     * @param {string}          selector
     * @param {object}          options - Dictionary of keyword arguments.  
     * @param {jQuery}          options.events - selector of Events
     * @param {KeyboardManager} options.keyboard_manager
     * @param {Contents}        options.contents
     * @param {SaveWidget}      options.save_widget
     * @param {object}          options.config
     * @param {string}          options.base_url
     * @param {string}          options.notebook_path
     * @param {string}          options.notebook_name
     */
    var Notebook = function (selector, options) {
        this.config = options.config;
        this.class_config = new configmod.ConfigWithDefaults(this.config, 
                                        Notebook.options_default, 'Notebook');
        this.base_url = options.base_url;
        this.notebook_path = options.notebook_path;
        this.notebook_name = options.notebook_name;
        this.events = options.events;
        this.keyboard_manager = options.keyboard_manager;
        this.contents = options.contents;
        this.save_widget = options.save_widget;
        this.tooltip = new tooltip.Tooltip(this.events);
        this.ws_url = options.ws_url;
        this._session_starting = false;
        this.last_modified = null;

        //  Create default scroll manager.
        this.scroll_manager = new scrollmanager.ScrollManager(this);

        // TODO: This code smells (and the other `= this` line a couple lines down)
        // We need a better way to deal with circular instance references.
        this.keyboard_manager.notebook = this;
        this.save_widget.notebook = this;
        
        mathjaxutils.init();

        if (marked) {
            marked.setOptions({
                gfm : true,
                tables: true,
                // FIXME: probably want central config for CodeMirror theme when we have js config
                langPrefix: "cm-s-ipython language-",
                highlight: function(code, lang, callback) {
                    if (!lang) {
                        // no language, no highlight
                        if (callback) {
                            callback(null, code);
                            return;
                        } else {
                            return code;
                        }
                    }
                    utils.requireCodeMirrorMode(lang, function (spec) {
                        var el = document.createElement("div");
                        var mode = CodeMirror.getMode({}, spec);
                        if (!mode) {
                            console.log("No CodeMirror mode: " + lang);
                            callback(null, code);
                            return;
                        }
                        try {
                            CodeMirror.runMode(code, spec, el);
                            callback(null, el.innerHTML);
                        } catch (err) {
                            console.log("Failed to highlight " + lang + " code", err);
                            callback(err, code);
                        }
                    }, function (err) {
                        console.log("No CodeMirror mode: " + lang);
                        callback(err, code);
                    });
                }
            });
        }

        this.element = $(selector);
        this.element.scroll();
        this.element.data("notebook", this);
        this.next_prompt_number = 1;
        this.session = null;
        this.kernel = null;
        this.clipboard = null;
        this.undelete_backup = null;
        this.undelete_index = null;
        this.undelete_below = false;
        this.paste_enabled = false;
        this.writable = false;
        // It is important to start out in command mode to match the intial mode
        // of the KeyboardManager.
        this.mode = 'command';
        this.set_dirty(false);
        this.metadata = {};
        this._checkpoint_after_save = false;
        this.last_checkpoint = null;
        this.checkpoints = [];
        this.autosave_interval = 0;
        this.autosave_timer = null;
        // autosave *at most* every two minutes
        this.minimum_autosave_interval = 120000;
        this.notebook_name_blacklist_re = /[\/\\:]/;
        this.nbformat = 4; // Increment this when changing the nbformat
        this.nbformat_minor = this.current_nbformat_minor = 0; // Increment this when changing the nbformat
        this.codemirror_mode = 'ipython';
        this.create_elements();
        this.bind_events();
        this.kernel_selector = null;
        this.dirty = null;
        this.trusted = null;
        this._fully_loaded = false;

        // Trigger cell toolbar registration.
        default_celltoolbar.register(this);
        rawcell_celltoolbar.register(this);
        slideshow_celltoolbar.register(this);

        // prevent assign to miss-typed properties.
        Object.seal(this);
    };

    Notebook.options_default = {
        // can be any cell type, or the special values of
        // 'above', 'below', or 'selected' to get the value from another cell.
        default_cell_type: 'code'
    };

    /**
     * Create an HTML and CSS representation of the notebook.
     */
    Notebook.prototype.create_elements = function () {
        var that = this;
        this.element.attr('tabindex','-1');
        this.container = $("<div/>").addClass("container").attr("id", "notebook-container");
        // We add this end_space div to the end of the notebook div to:
        // i) provide a margin between the last cell and the end of the notebook
        // ii) to prevent the div from scrolling up when the last cell is being
        // edited, but is too low on the page, which browsers will do automatically.
        var end_space = $('<div/>').addClass('end_space');
        end_space.dblclick(function (e) {
            var ncells = that.ncells();
            that.insert_cell_below('code',ncells-1);
        });
        this.element.append(this.container);
        this.container.after(end_space);
    };

    /**
     * Bind JavaScript events: key presses and custom IPython events.
     */
    Notebook.prototype.bind_events = function () {
        var that = this;

        this.events.on('set_next_input.Notebook', function (event, data) {
            if (data.replace) {
                data.cell.set_text(data.text);
                data.cell.clear_output();
            } else {
                var index = that.find_cell_index(data.cell);
                var new_cell = that.insert_cell_below('code',index);
                new_cell.set_text(data.text);
            }
            that.dirty = true;
        });

        this.events.on('unrecognized_cell.Cell', function () {
            that.warn_nbformat_minor();
        });

        this.events.on('unrecognized_output.OutputArea', function () {
            that.warn_nbformat_minor();
        });

        this.events.on('set_dirty.Notebook', function (event, data) {
            that.dirty = data.value;
        });

        this.events.on('trust_changed.Notebook', function (event, trusted) {
            that.trusted = trusted;
        });

        this.events.on('select.Cell', function (event, data) {
            var index = that.find_cell_index(data.cell);
            that.select(index);
        });

        this.events.on('edit_mode.Cell', function (event, data) {
            that.handle_edit_mode(data.cell);
        });

        this.events.on('command_mode.Cell', function (event, data) {
            that.handle_command_mode(data.cell);
        });
        
        this.events.on('spec_changed.Kernel', function(event, data) {
            that.metadata.kernelspec = {
                name: data.name,
                display_name: data.spec.display_name,
                language: data.spec.language,
            };
            // start session if the current session isn't already correct
            if (!(that.session && that.session.kernel && that.session.kernel.name === data.name)) {
                that.start_session(data.name);
            }
        });

        this.events.on('kernel_ready.Kernel', function(event, data) {
            var kinfo = data.kernel.info_reply;
            if (!kinfo.language_info) {
                delete that.metadata.language_info;
                return;
            }
            var langinfo = kinfo.language_info;
            that.metadata.language_info = langinfo;
            // Mode 'null' should be plain, unhighlighted text.
            var cm_mode = langinfo.codemirror_mode || langinfo.name || 'null';
            that.set_codemirror_mode(cm_mode);
        });

        var collapse_time = function (time) {
            var app_height = $('#ipython-main-app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var new_height = app_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, time);
        };

        this.element.bind('collapse_pager', function (event, extrap) {
            var time = (extrap !== undefined) ? ((extrap.duration !== undefined ) ? extrap.duration : 'fast') : 'fast';
            collapse_time(time);
        });

        var expand_time = function (time) {
            var app_height = $('#ipython-main-app').height(); // content height
            var splitter_height = $('div#pager_splitter').outerHeight(true);
            var pager_height = $('div#pager').outerHeight(true);
            var new_height = app_height - pager_height - splitter_height;
            that.element.animate({height : new_height + 'px'}, time);
        };

        this.element.bind('expand_pager', function (event, extrap) {
            var time = (extrap !== undefined) ? ((extrap.duration !== undefined ) ? extrap.duration : 'fast') : 'fast';
            expand_time(time);
        });
        
        // Firefox 22 broke $(window).on("beforeunload")
        // I'm not sure why or how.
        window.onbeforeunload = function (e) {
            // TODO: Make killing the kernel configurable.
            var kill_kernel = false;
            if (kill_kernel) {
                that.session.delete();
            }
            // if we are autosaving, trigger an autosave on nav-away.
            // still warn, because if we don't the autosave may fail.
            if (that.dirty) {
                if ( that.autosave_interval ) {
                    // schedule autosave in a timeout
                    // this gives you a chance to forcefully discard changes
                    // by reloading the page if you *really* want to.
                    // the timer doesn't start until you *dismiss* the dialog.
                    setTimeout(function () {
                        if (that.dirty) {
                            that.save_notebook();
                        }
                    }, 1000);
                    return "Autosave in progress, latest changes may be lost.";
                } else {
                    return "Unsaved changes will be lost.";
                }
            }
            // IE treats null as a string.  Instead just return which will avoid the dialog.
            return;
        };
    };
    
    /**
     * Trigger a warning dialog about missing functionality from newer minor versions
     */
    Notebook.prototype.warn_nbformat_minor = function (event) {
        var v = 'v' + this.nbformat + '.';
        var orig_vs = v + this.nbformat_minor;
        var this_vs = v + this.current_nbformat_minor;
        var msg = "This notebook is version " + orig_vs + ", but we only fully support up to " +
        this_vs + ".  You can still work with this notebook, but cell and output types " +
        "introduced in later notebook versions will not be available.";

        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title : "Newer Notebook",
            body : msg,
            buttons : {
                OK : {
                    "class" : "btn-danger"
                }
            }
        });
    };

    /**
     * Set the dirty flag, and trigger the set_dirty.Notebook event
     */
    Notebook.prototype.set_dirty = function (value) {
        if (value === undefined) {
            value = true;
        }
        if (this.dirty === value) {
            return;
        }
        this.events.trigger('set_dirty.Notebook', {value: value});
    };

    /**
     * Scroll the top of the page to a given cell.
     * 
     * @param {integer}  index - An index of the cell to view
     * @param {integer}  time - Animation time in milliseconds
     * @return {integer} Pixel offset from the top of the container
     */
    Notebook.prototype.scroll_to_cell = function (index, time) {
        var cells = this.get_cells();
        time = time || 0;
        index = Math.min(cells.length-1,index);
        index = Math.max(0             ,index);
        var scroll_value = cells[index].element.position().top-cells[0].element.position().top ;
        this.scroll_manager.element.animate({scrollTop:scroll_value}, time);
        return scroll_value;
    };

    /**
     * Scroll to the bottom of the page.
     */
    Notebook.prototype.scroll_to_bottom = function () {
        this.scroll_manager.element.animate({scrollTop:this.element.get(0).scrollHeight}, 0);
    };

    /**
     * Scroll to the top of the page.
     */
    Notebook.prototype.scroll_to_top = function () {
        this.scroll_manager.element.animate({scrollTop:0}, 0);
    };

    // Edit Notebook metadata

    /**
     * Display a dialog that allows the user to edit the Notebook's metadata.
     */
    Notebook.prototype.edit_metadata = function () {
        var that = this;
        dialog.edit_metadata({
            md: this.metadata, 
            callback: function (md) {
                that.metadata = md;
            },
            name: 'Notebook',
            notebook: this,
            keyboard_manager: this.keyboard_manager});
    };

    // Cell indexing, retrieval, etc.

    /**
     * Get all cell elements in the notebook.
     * 
     * @return {jQuery} A selector of all cell elements
     */
    Notebook.prototype.get_cell_elements = function () {
        return this.container.find(".cell").not('.cell .cell');
    };

    /**
     * Get a particular cell element.
     * 
     * @param {integer} index An index of a cell to select
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
     * Try to get a particular cell by msg_id.
     * 
     * @param {string} msg_id A message UUID
     * @return {Cell} Cell or null if no cell was found.
     */
    Notebook.prototype.get_msg_cell = function (msg_id) {
        return codecell.CodeCell.msg_cells[msg_id] || null;
    };

    /**
     * Count the cells in this notebook.
     * 
     * @return {integer} The number of cells in this notebook
     */
    Notebook.prototype.ncells = function () {
        return this.get_cell_elements().length;
    };

    /**
     * Get all Cell objects in this notebook.
     * 
     * @return {Array} This notebook's Cell objects
     */
    Notebook.prototype.get_cells = function () {
        // TODO: we are often calling cells as cells()[i], which we should optimize
        // to cells(i) or a new method.
        return this.get_cell_elements().toArray().map(function (e) {
            return $(e).data("cell");
        });
    };

    /**
     * Get a Cell objects from this notebook.
     * 
     * @param {integer} index - An index of a cell to retrieve
     * @return {Cell} Cell or null if no cell was found.
     */
    Notebook.prototype.get_cell = function (index) {
        var result = null;
        var ce = this.get_cell_element(index);
        if (ce !== null) {
            result = ce.data('cell');
        }
        return result;
    };

    /**
     * Get the cell below a given cell.
     * 
     * @param {Cell} cell
     * @return {Cell} the next cell or null if no cell was found.
     */
    Notebook.prototype.get_next_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (this.is_valid_cell_index(index+1)) {
            result = this.get_cell(index+1);
        }
        return result;
    };

    /**
     * Get the cell above a given cell.
     * 
     * @param {Cell} cell
     * @return {Cell} The previous cell or null if no cell was found.
     */
    Notebook.prototype.get_prev_cell = function (cell) {
        var result = null;
        var index = this.find_cell_index(cell);
        if (index !== null && index > 0) {
            result = this.get_cell(index-1);
        }
        return result;
    };
    
    /**
     * Get the numeric index of a given cell.
     * 
     * @param {Cell} cell
     * @return {integer} The cell's numeric index or null if no cell was found.
     */
    Notebook.prototype.find_cell_index = function (cell) {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell") === cell) {
                result = index;
            }
        });
        return result;
    };

    /**
     * Return given index if defined, or the selected index if not.
     * 
     * @param {integer} [index] - A cell's index
     * @return {integer} cell index
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
     * 
     * @return {Cell} The selected cell
     */
    Notebook.prototype.get_selected_cell = function () {
        var index = this.get_selected_index();
        return this.get_cell(index);
    };

    /**
     * Check whether a cell index is valid.
     * 
     * @param {integer} index - A cell index
     * @return True if the index is valid, false otherwise
     */
    Notebook.prototype.is_valid_cell_index = function (index) {
        if (index !== null && index >= 0 && index < this.ncells()) {
            return true;
        } else {
            return false;
        }
    };

    /**
     * Get the index of the currently selected cell.
     *
     * @return {integer} The selected cell's numeric index
     */
    Notebook.prototype.get_selected_index = function () {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell").selected === true) {
                result = index;
            }
        });
        return result;
    };


    // Cell selection.

    /**
     * Programmatically select a cell.
     * 
     * @param {integer} index - A cell's index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.select = function (index) {
        if (this.is_valid_cell_index(index)) {
            var sindex = this.get_selected_index();
            if (sindex !== null && index !== sindex) {
                // If we are about to select a different cell, make sure we are
                // first in command mode.
                if (this.mode !== 'command') {
                    this.command_mode();
                }
                this.get_cell(sindex).unselect();
            }
            var cell = this.get_cell(index);
            cell.select();
            if (cell.cell_type === 'heading') {
                this.events.trigger('selected_cell_type_changed.Notebook',
                    {'cell_type':cell.cell_type,level:cell.level}
                );
            } else {
                this.events.trigger('selected_cell_type_changed.Notebook',
                    {'cell_type':cell.cell_type}
                );
            }
        }
        return this;
    };

    /**
     * Programmatically select the next cell.
     *
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
     * @return {Notebook} This notebook
     */
    Notebook.prototype.select_prev = function () {
        var index = this.get_selected_index();
        this.select(index-1);
        return this;
    };


    // Edit/Command mode

    /**
     * Gets the index of the cell that is in edit mode.
     *
     * @return {integer} index
     */
    Notebook.prototype.get_edit_index = function () {
        var result = null;
        this.get_cell_elements().filter(function (index) {
            if ($(this).data("cell").mode === 'edit') {
                result = index;
            }
        });
        return result;
    };

    /**
     * Handle when a a cell blurs and the notebook should enter command mode.
     *
     * @param {Cell} [cell] - Cell to enter command mode on.
     */
    Notebook.prototype.handle_command_mode = function (cell) {
        if (this.mode !== 'command') {
            cell.command_mode();
            this.mode = 'command';
            this.events.trigger('command_mode.Notebook');
            this.keyboard_manager.command_mode();
        }
    };

    /**
     * Make the notebook enter command mode.
     */
    Notebook.prototype.command_mode = function () {
        var cell = this.get_cell(this.get_edit_index());
        if (cell && this.mode !== 'command') {
            // We don't call cell.command_mode, but rather blur the CM editor
            // which will trigger the call to handle_command_mode.
            cell.code_mirror.getInputField().blur();
        }
    };

    /**
     * Handle when a cell fires it's edit_mode event.
     *
     * @param {Cell} [cell] Cell to enter edit mode on.
     */
    Notebook.prototype.handle_edit_mode = function (cell) {
        if (cell && this.mode !== 'edit') {
            cell.edit_mode();
            this.mode = 'edit';
            this.events.trigger('edit_mode.Notebook');
            this.keyboard_manager.edit_mode();
        }
    };

    /**
     * Make a cell enter edit mode.
     */
    Notebook.prototype.edit_mode = function () {
        var cell = this.get_selected_cell();
        if (cell && this.mode !== 'edit') {
            cell.unrender();
            cell.focus_editor();
        }
    };
    
    /**
     * Ensure either cell, or codemirror is focused. Is none 
     * is focused, focus the cell.
     */
    Notebook.prototype.ensure_focused = function(){
        var cell = this.get_selected_cell();
        if (cell === null) {return;}  // No cell is selected
        cell.ensure_focused();
    }

    /**
     * Focus the currently selected cell.
     */
    Notebook.prototype.focus_cell = function () {
        var cell = this.get_selected_cell();
        if (cell === null) {return;}  // No cell is selected
        cell.focus_cell();
    };

    // Cell movement

    /**
     * Move given (or selected) cell up and select it.
     * 
     * @param {integer} [index] - cell index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.move_cell_up = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i) && i > 0) {
            var pivot = this.get_cell_element(i-1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.before(tomove);
                this.select(i-1);
                var cell = this.get_selected_cell();
                cell.focus_cell();
            }
            this.set_dirty(true);
        }
        return this;
    };


    /**
     * Move given (or selected) cell down and select it.
     * 
     * @param {integer} [index] - cell index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.move_cell_down = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i) && this.is_valid_cell_index(i+1)) {
            var pivot = this.get_cell_element(i+1);
            var tomove = this.get_cell_element(i);
            if (pivot !== null && tomove !== null) {
                tomove.detach();
                pivot.after(tomove);
                this.select(i+1);
                var cell = this.get_selected_cell();
                cell.focus_cell();
            }
        }
        this.set_dirty();
        return this;
    };


    // Insertion, deletion.

    /**
     * Delete a cell from the notebook without any precautions
     * Needed to reload checkpoints and other things like that.
     * 
     * @param {integer} [index] - cell's numeric index
     * @return {Notebook} This notebook
     */
    Notebook.prototype._unsafe_delete_cell = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);

        $('#undelete_cell').addClass('disabled');
        if (this.is_valid_cell_index(i)) {
            var old_ncells = this.ncells();
            var ce = this.get_cell_element(i);
            ce.remove();
            this.set_dirty(true);
        }
        return this;
    };

    /**
     * Delete a cell from the notebook.
     * 
     * @param {integer} [index] - cell's numeric index
     * @return {Notebook} This notebook
     */
    Notebook.prototype.delete_cell = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (!cell.is_deletable()) {
            return this;
        }

        this.undelete_backup = cell.toJSON();
        $('#undelete_cell').removeClass('disabled');
        if (this.is_valid_cell_index(i)) {
            var old_ncells = this.ncells();
            var ce = this.get_cell_element(i);
            ce.remove();
            if (i === 0) {
                // Always make sure we have at least one cell.
                if (old_ncells === 1) {
                    this.insert_cell_below('code');
                }
                this.select(0);
                this.undelete_index = 0;
                this.undelete_below = false;
            } else if (i === old_ncells-1 && i !== 0) {
                this.select(i-1);
                this.undelete_index = i - 1;
                this.undelete_below = true;
            } else {
                this.select(i);
                this.undelete_index = i;
                this.undelete_below = false;
            }
            this.events.trigger('delete.Cell', {'cell': cell, 'index': i});
            this.set_dirty(true);
        }
        return this;
    };

    /**
     * Restore the most recently deleted cell.
     */
    Notebook.prototype.undelete_cell = function() {
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
            if (this.undelete_below) {
                this.select(current_index+1);
            } else {
                this.select(current_index);
            }
            this.undelete_backup = null;
            this.undelete_index = null;
        }
        $('#undelete_cell').addClass('disabled');
    };

    /**
     * Insert a cell so that after insertion the cell is at given index.
     *
     * If cell type is not provided, it will default to the type of the
     * currently active cell.
     *
     * Similar to insert_above, but index parameter is mandatory.
     *
     * Index will be brought back into the accessible range [0,n].
     *
     * @param {string} [type] - in ['code','markdown', 'raw'], defaults to 'code'
     * @param {integer} [index] - a valid index where to insert cell
     * @return {Cell|null} created cell or null
     */
    Notebook.prototype.insert_cell_at_index = function(type, index){

        var ncells = this.ncells();
        index = Math.min(index, ncells);
        index = Math.max(index, 0);
        var cell = null;
        type = type || this.class_config.get_sync('default_cell_type');
        if (type === 'above') {
            if (index > 0) {
                type = this.get_cell(index-1).cell_type;
            } else {
                type = 'code';
            }
        } else if (type === 'below') {
            if (index < ncells) {
                type = this.get_cell(index).cell_type;
            } else {
                type = 'code';
            }
        } else if (type === 'selected') {
            type = this.get_selected_cell().cell_type;
        }

        if (ncells === 0 || this.is_valid_cell_index(index) || index === ncells) {
            var cell_options = {
                events: this.events, 
                config: this.config, 
                keyboard_manager: this.keyboard_manager, 
                notebook: this,
                tooltip: this.tooltip
            };
            switch(type) {
            case 'code':
                cell = new codecell.CodeCell(this.kernel, cell_options);
                cell.set_input_prompt();
                break;
            case 'markdown':
                cell = new textcell.MarkdownCell(cell_options);
                break;
            case 'raw':
                cell = new textcell.RawCell(cell_options);
                break;
            default:
                console.log("Unrecognized cell type: ", type, cellmod);
                cell = new cellmod.UnrecognizedCell(cell_options);
            }

            if(this._insert_element_at_index(cell.element,index)) {
                cell.render();
                this.events.trigger('create.Cell', {'cell': cell, 'index': index});
                cell.refresh();
                // We used to select the cell after we refresh it, but there
                // are now cases were this method is called where select is
                // not appropriate. The selection logic should be handled by the
                // caller of the the top level insert_cell methods.
                this.set_dirty(true);
            }
        }
        return cell;

    };

    /**
     * Insert an element at given cell index.
     *
     * @param {HTMLElement} element - a cell element
     * @param {integer}     [index] - a valid index where to inser cell
     * @returns {boolean}   success
     */
    Notebook.prototype._insert_element_at_index = function(element, index){
        if (element === undefined){
            return false;
        }

        var ncells = this.ncells();

        if (ncells === 0) {
            // special case append if empty
            this.container.append(element);
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
     * @param {string}     [type] - cell type
     * @param {integer}    [index] - defaults to the currently selected cell
     * @return {Cell|null} handle to created cell or null
     */
    Notebook.prototype.insert_cell_above = function (type, index) {
        index = this.index_or_selected(index);
        return this.insert_cell_at_index(type, index);
    };

    /**
     * Insert a cell of given type below given index, or at bottom
     * of notebook if index greater than number of cells
     *
     * @param {string}     [type] - cell type
     * @param {integer}    [index] - defaults to the currently selected cell
     * @return {Cell|null} handle to created cell or null
     */
    Notebook.prototype.insert_cell_below = function (type, index) {
        index = this.index_or_selected(index);
        return this.insert_cell_at_index(type, index+1);
    };


    /**
     * Insert cell at end of notebook
     *
     * @param {string} type - cell type
     * @return {Cell|null} handle to created cell or null
     */
    Notebook.prototype.insert_cell_at_bottom = function (type){
        var len = this.ncells();
        return this.insert_cell_below(type,len-1);
    };

    /**
     * Turn a cell into a code cell.
     * 
     * @param {integer} [index] - cell index
     */
    Notebook.prototype.to_code = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_cell = this.get_cell(i);
            if (!(source_cell instanceof codecell.CodeCell)) {
                var target_cell = this.insert_cell_below('code',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                }
                //metadata
                target_cell.metadata = source_cell.metadata;

                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_cell.element.remove();
                this.select(i);
                var cursor = source_cell.code_mirror.getCursor();
                target_cell.code_mirror.setCursor(cursor);
                this.set_dirty(true);
            }
        }
    };

    /**
     * Turn a cell into a Markdown cell.
     * 
     * @param {integer} [index] - cell index
     */
    Notebook.prototype.to_markdown = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var source_cell = this.get_cell(i);

            if (!(source_cell instanceof textcell.MarkdownCell)) {
                var target_cell = this.insert_cell_below('markdown',i);
                var text = source_cell.get_text();

                if (text === source_cell.placeholder) {
                    text = '';
                }
                // metadata
                target_cell.metadata = source_cell.metadata;
                // We must show the editor before setting its contents
                target_cell.unrender();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_cell.element.remove();
                this.select(i);
                if ((source_cell instanceof textcell.TextCell) && source_cell.rendered) {
                    target_cell.render();
                }
                var cursor = source_cell.code_mirror.getCursor();
                target_cell.code_mirror.setCursor(cursor);
                this.set_dirty(true);
            }
        }
    };

    /**
     * Turn a cell into a raw text cell.
     * 
     * @param {integer} [index] - cell index
     */
    Notebook.prototype.to_raw = function (index) {
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var target_cell = null;
            var source_cell = this.get_cell(i);

            if (!(source_cell instanceof textcell.RawCell)) {
                target_cell = this.insert_cell_below('raw',i);
                var text = source_cell.get_text();
                if (text === source_cell.placeholder) {
                    text = '';
                }
                //metadata
                target_cell.metadata = source_cell.metadata;
                // We must show the editor before setting its contents
                target_cell.unrender();
                target_cell.set_text(text);
                // make this value the starting point, so that we can only undo
                // to this state, instead of a blank cell
                target_cell.code_mirror.clearHistory();
                source_cell.element.remove();
                this.select(i);
                var cursor = source_cell.code_mirror.getCursor();
                target_cell.code_mirror.setCursor(cursor);
                this.set_dirty(true);
            }
        }
    };
    
    /**
     * Warn about heading cell support removal.
     */
    Notebook.prototype._warn_heading = function () {
        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title : "Use markdown headings",
            body : $("<p/>").text(
                'IPython no longer uses special heading cells. ' + 
                'Instead, write your headings in Markdown cells using # characters:'
            ).append($('<pre/>').text(
                '## This is a level 2 heading'
            )),
            buttons : {
                "OK" : {}
            }
        });
    };
    
    /**
     * Turn a cell into a heading containing markdown cell.
     * 
     * @param {integer} [index] - cell index
     * @param {integer} [level] - heading level (e.g., 1 for h1)
     */
    Notebook.prototype.to_heading = function (index, level) {
        this.to_markdown(index);
        level = level || 1;
        var i = this.index_or_selected(index);
        if (this.is_valid_cell_index(i)) {
            var cell = this.get_cell(i);
            cell.set_heading_level(level);
            this.set_dirty(true);
        }
    };


    // Cut/Copy/Paste

    /**
     * Enable the UI elements for pasting cells.
     */
    Notebook.prototype.enable_paste = function () {
        var that = this;
        if (!this.paste_enabled) {
            $('#paste_cell_replace').removeClass('disabled')
                .on('click', function () {that.paste_cell_replace();});
            $('#paste_cell_above').removeClass('disabled')
                .on('click', function () {that.paste_cell_above();});
            $('#paste_cell_below').removeClass('disabled')
                .on('click', function () {that.paste_cell_below();});
            this.paste_enabled = true;
        }
    };

    /**
     * Disable the UI elements for pasting cells.
     */
    Notebook.prototype.disable_paste = function () {
        if (this.paste_enabled) {
            $('#paste_cell_replace').addClass('disabled').off('click');
            $('#paste_cell_above').addClass('disabled').off('click');
            $('#paste_cell_below').addClass('disabled').off('click');
            this.paste_enabled = false;
        }
    };

    /**
     * Cut a cell.
     */
    Notebook.prototype.cut_cell = function () {
        this.copy_cell();
        this.delete_cell();
    };

    /**
     * Copy a cell.
     */
    Notebook.prototype.copy_cell = function () {
        var cell = this.get_selected_cell();
        this.clipboard = cell.toJSON();
        // remove undeletable status from the copied cell
        if (this.clipboard.metadata.deletable !== undefined) {
            delete this.clipboard.metadata.deletable;
        }
        this.enable_paste();
    };

    /**
     * Replace the selected cell with the cell in the clipboard.
     */
    Notebook.prototype.paste_cell_replace = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            var old_cell = this.get_next_cell(new_cell);
            this.delete_cell(this.find_cell_index(old_cell));
            this.select(this.find_cell_index(new_cell));
        }
    };

    /**
     * Paste a cell from the clipboard above the selected cell.
     */
    Notebook.prototype.paste_cell_above = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_above(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            new_cell.focus_cell();
        }
    };

    /**
     * Paste a cell from the clipboard below the selected cell.
     */
    Notebook.prototype.paste_cell_below = function () {
        if (this.clipboard !== null && this.paste_enabled) {
            var cell_data = this.clipboard;
            var new_cell = this.insert_cell_below(cell_data.cell_type);
            new_cell.fromJSON(cell_data);
            new_cell.focus_cell();
        }
    };

    // Split/merge

    /**
     * Split the selected cell into two cells.
     */
    Notebook.prototype.split_cell = function () {
        var cell = this.get_selected_cell();
        if (cell.is_splittable()) {
            var texta = cell.get_pre_cursor();
            var textb = cell.get_post_cursor();
            cell.set_text(textb);
            var new_cell = this.insert_cell_above(cell.cell_type);
            // Unrender the new cell so we can call set_text.
            new_cell.unrender();
            new_cell.set_text(texta);
        }
    };

    /**
     * Merge the selected cell into the cell above it.
     */
    Notebook.prototype.merge_cell_above = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        var render = cell.rendered;
        if (!cell.is_mergeable()) {
            return;
        }
        if (index > 0) {
            var upper_cell = this.get_cell(index-1);
            if (!upper_cell.is_mergeable()) {
                return;
            }
            var upper_text = upper_cell.get_text();
            var text = cell.get_text();
            if (cell instanceof codecell.CodeCell) {
                cell.set_text(upper_text+'\n'+text);
            } else {
                cell.unrender(); // Must unrender before we set_text.
                cell.set_text(upper_text+'\n\n'+text);
                if (render) {
                    // The rendered state of the final cell should match
                    // that of the original selected cell;
                    cell.render();
                }
            }
            this.delete_cell(index-1);
            this.select(this.find_cell_index(cell));
        }
    };

    /**
     * Merge the selected cell into the cell below it.
     */
    Notebook.prototype.merge_cell_below = function () {
        var index = this.get_selected_index();
        var cell = this.get_cell(index);
        var render = cell.rendered;
        if (!cell.is_mergeable()) {
            return;
        }
        if (index < this.ncells()-1) {
            var lower_cell = this.get_cell(index+1);
            if (!lower_cell.is_mergeable()) {
                return;
            }
            var lower_text = lower_cell.get_text();
            var text = cell.get_text();
            if (cell instanceof codecell.CodeCell) {
                cell.set_text(text+'\n'+lower_text);
            } else {
                cell.unrender(); // Must unrender before we set_text.
                cell.set_text(text+'\n\n'+lower_text);
                if (render) {
                    // The rendered state of the final cell should match
                    // that of the original selected cell;
                    cell.render();
                }
            }
            this.delete_cell(index+1);
            this.select(this.find_cell_index(cell));
        }
    };


    // Cell collapsing and output clearing

    /**
     * Hide a cell's output.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.collapse_output = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.collapse_output();
            this.set_dirty(true);
        }
    };

    /**
     * Hide each code cell's output area.
     */
    Notebook.prototype.collapse_all_output = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.collapse_output();
            }
        });
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /**
     * Show a cell's output.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.expand_output = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.expand_output();
            this.set_dirty(true);
        }
    };

    /**
     * Expand each code cell's output area, and remove scrollbars.
     */
    Notebook.prototype.expand_all_output = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.expand_output();
            }
        });
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /**
     * Clear the selected CodeCell's output area.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.clear_output = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.clear_output();
            this.set_dirty(true);
        }
    };

    /**
     * Clear each code cell's output area.
     */
    Notebook.prototype.clear_all_output = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.clear_output();
            }
        });
        this.set_dirty(true);
    };

    /**
     * Scroll the selected CodeCell's output area.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.scroll_output = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.scroll_output();
            this.set_dirty(true);
        }
    };

    /**
     * Expand each code cell's output area and add a scrollbar for long output.
     */
    Notebook.prototype.scroll_all_output = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.scroll_output();
            }
        });
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /** 
     * Toggle whether a cell's output is collapsed or expanded.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.toggle_output = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.toggle_output();
            this.set_dirty(true);
        }
    };

    /**
     * Toggle the output of all cells.
     */
    Notebook.prototype.toggle_all_output = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.toggle_output();
            }
        });
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    /**
     * Toggle a scrollbar for long cell outputs.
     * 
     * @param {integer} index - cell index
     */
    Notebook.prototype.toggle_output_scroll = function (index) {
        var i = this.index_or_selected(index);
        var cell = this.get_cell(i);
        if (cell !== null && (cell instanceof codecell.CodeCell)) {
            cell.toggle_output_scroll();
            this.set_dirty(true);
        }
    };

    /**
     * Toggle the scrolling of long output on all cells.
     */
    Notebook.prototype.toggle_all_output_scroll = function () {
        this.get_cells().map(function (cell, i) {
            if (cell instanceof codecell.CodeCell) {
                cell.toggle_output_scroll();
            }
        });
        // this should not be set if the `collapse` key is removed from nbformat
        this.set_dirty(true);
    };

    // Other cell functions: line numbers, ...

    /**
     * Toggle line numbers in the selected cell's input area.
     */
    Notebook.prototype.cell_toggle_line_numbers = function() {
        this.get_selected_cell().toggle_line_numbers();
    };
    
    /**
     * Set the codemirror mode for all code cells, including the default for
     * new code cells.
     */
    Notebook.prototype.set_codemirror_mode = function(newmode){
        if (newmode === this.codemirror_mode) {
            return;
        }
        this.codemirror_mode = newmode;
        codecell.CodeCell.options_default.cm_config.mode = newmode;
        
        var that = this;
        utils.requireCodeMirrorMode(newmode, function (spec) {
            that.get_cells().map(function(cell, i) {
                if (cell.cell_type === 'code'){
                    cell.code_mirror.setOption('mode', spec);
                    // This is currently redundant, because cm_config ends up as
                    // codemirror's own .options object, but I don't want to
                    // rely on that.
                    cell.cm_config.mode = spec;
                }
            });
        });
    };

    // Session related things

    /**
     * Start a new session and set it on each code cell.
     */
    Notebook.prototype.start_session = function (kernel_name) {
        if (this._session_starting) {
            throw new session.SessionAlreadyStarting();
        }
        this._session_starting = true;

        var options = {
            base_url: this.base_url,
            ws_url: this.ws_url,
            notebook_path: this.notebook_path,
            notebook_name: this.notebook_name,
            kernel_name: kernel_name,
            notebook: this
        };

        var success = $.proxy(this._session_started, this);
        var failure = $.proxy(this._session_start_failed, this);

        if (this.session !== null) {
            this.session.restart(options, success, failure);
        } else {
            this.session = new session.Session(options);
            this.session.start(success, failure);
        }
    };


    /**
     * Once a session is started, link the code cells to the kernel and pass the 
     * comm manager to the widget manager.
     */
    Notebook.prototype._session_started = function (){
        this._session_starting = false;
        this.kernel = this.session.kernel;
        var ncells = this.ncells();
        for (var i=0; i<ncells; i++) {
            var cell = this.get_cell(i);
            if (cell instanceof codecell.CodeCell) {
                cell.set_kernel(this.session.kernel);
            }
        }
    };

    /**
     * Called when the session fails to start.
     */
    Notebook.prototype._session_start_failed = function(jqxhr, status, error){
        this._session_starting = false;
        utils.log_ajax_error(jqxhr, status, error);
    };
    
    /**
     * Prompt the user to restart the IPython kernel.
     */
    Notebook.prototype.restart_kernel = function () {
        var that = this;
        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title : "Restart kernel or continue running?",
            body : $("<p/>").text(
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
     * Execute or render cell outputs and go into command mode.
     */
    Notebook.prototype.execute_cell = function () {
        // mode = shift, ctrl, alt
        var cell = this.get_selected_cell();
        
        cell.execute();
        this.command_mode();
        this.set_dirty(true);
    };

    /**
     * Execute or render cell outputs and insert a new cell below.
     */
    Notebook.prototype.execute_cell_and_insert_below = function () {
        var cell = this.get_selected_cell();
        var cell_index = this.find_cell_index(cell);
        
        cell.execute();

        // If we are at the end always insert a new cell and return
        if (cell_index === (this.ncells()-1)) {
            this.command_mode();
            this.insert_cell_below();
            this.select(cell_index+1);
            this.edit_mode();
            this.scroll_to_bottom();
            this.set_dirty(true);
            return;
        }

        this.command_mode();
        this.insert_cell_below();
        this.select(cell_index+1);
        this.edit_mode();
        this.set_dirty(true);
    };

    /**
     * Execute or render cell outputs and select the next cell.
     */
    Notebook.prototype.execute_cell_and_select_below = function () {

        var cell = this.get_selected_cell();
        var cell_index = this.find_cell_index(cell);
        
        cell.execute();

        // If we are at the end always insert a new cell and return
        if (cell_index === (this.ncells()-1)) {
            this.command_mode();
            this.insert_cell_below();
            this.select(cell_index+1);
            this.edit_mode();
            this.scroll_to_bottom();
            this.set_dirty(true);
            return;
        }

        this.command_mode();
        this.select(cell_index+1);
        this.focus_cell();
        this.set_dirty(true);
    };

    /**
     * Execute all cells below the selected cell.
     */
    Notebook.prototype.execute_cells_below = function () {
        this.execute_cell_range(this.get_selected_index(), this.ncells());
        this.scroll_to_bottom();
    };

    /**
     * Execute all cells above the selected cell.
     */
    Notebook.prototype.execute_cells_above = function () {
        this.execute_cell_range(0, this.get_selected_index());
    };

    /**
     * Execute all cells.
     */
    Notebook.prototype.execute_all_cells = function () {
        this.execute_cell_range(0, this.ncells());
        this.scroll_to_bottom();
    };

    /**
     * Execute a contiguous range of cells.
     * 
     * @param {integer} start - index of the first cell to execute (inclusive)
     * @param {integer} end - index of the last cell to execute (exclusive)
     */
    Notebook.prototype.execute_cell_range = function (start, end) {
        this.command_mode();
        for (var i=start; i<end; i++) {
            this.select(i);
            this.execute_cell();
        }
    };

    // Persistance and loading

    /**
     * Getter method for this notebook's name.
     * 
     * @return {string} This notebook's name (excluding file extension)
     */
    Notebook.prototype.get_notebook_name = function () {
        var nbname = this.notebook_name.substring(0,this.notebook_name.length-6);
        return nbname;
    };

    /**
     * Setter method for this notebook's name.
     *
     * @param {string} name
     */
    Notebook.prototype.set_notebook_name = function (name) {
        var parent = utils.url_path_split(this.notebook_path)[0];
        this.notebook_name = name;
        this.notebook_path = utils.url_path_join(parent, name);
    };

    /**
     * Check that a notebook's name is valid.
     * 
     * @param {string} nbname - A name for this notebook
     * @return {boolean} True if the name is valid, false if invalid
     */
    Notebook.prototype.test_notebook_name = function (nbname) {
        nbname = nbname || '';
        if (nbname.length>0 && !this.notebook_name_blacklist_re.test(nbname)) {
            return true;
        } else {
            return false;
        }
    };

    /**
     * Load a notebook from JSON (.ipynb).
     * 
     * @param {object} data - JSON representation of a notebook
     */
    Notebook.prototype.fromJSON = function (data) {

        var content = data.content;
        var ncells = this.ncells();
        var i;
        for (i=0; i<ncells; i++) {
            // Always delete cell 0 as they get renumbered as they are deleted.
            this._unsafe_delete_cell(0);
        }
        // Save the metadata and name.
        this.metadata = content.metadata;
        this.notebook_name = data.name;
        this.notebook_path = data.path;
        var trusted = true;
        
        // Set the codemirror mode from language_info metadata
        if (this.metadata.language_info !== undefined) {
            var langinfo = this.metadata.language_info;
            // Mode 'null' should be plain, unhighlighted text.
            var cm_mode = langinfo.codemirror_mode || langinfo.name || 'null';
            this.set_codemirror_mode(cm_mode);
        }
        
        var new_cells = content.cells;
        ncells = new_cells.length;
        var cell_data = null;
        var new_cell = null;
        for (i=0; i<ncells; i++) {
            cell_data = new_cells[i];
            new_cell = this.insert_cell_at_index(cell_data.cell_type, i);
            new_cell.fromJSON(cell_data);
            if (new_cell.cell_type === 'code' && !new_cell.output_area.trusted) {
                trusted = false;
            }
        }
        if (trusted !== this.trusted) {
            this.trusted = trusted;
            this.events.trigger("trust_changed.Notebook", trusted);
        }
    };

    /**
     * Dump this notebook into a JSON-friendly object.
     * 
     * @return {object} A JSON-friendly representation of this notebook.
     */
    Notebook.prototype.toJSON = function () {
        // remove the conversion indicator, which only belongs in-memory
        delete this.metadata.orig_nbformat;
        delete this.metadata.orig_nbformat_minor;

        var cells = this.get_cells();
        var ncells = cells.length;
        var cell_array = new Array(ncells);
        var trusted = true;
        for (var i=0; i<ncells; i++) {
            var cell = cells[i];
            if (cell.cell_type === 'code' && !cell.output_area.trusted) {
                trusted = false;
            }
            cell_array[i] = cell.toJSON();
        }
        var data = {
            cells: cell_array,
            metadata: this.metadata,
            nbformat: this.nbformat,
            nbformat_minor: this.nbformat_minor
        };
        if (trusted !== this.trusted) {
            this.trusted = trusted;
            this.events.trigger("trust_changed.Notebook", trusted);
        }
        return data;
    };

    /**
     * Start an autosave timer which periodically saves the notebook.
     * 
     * @param {integer} interval - the autosave interval in milliseconds
     */
    Notebook.prototype.set_autosave_interval = function (interval) {
        var that = this;
        // clear previous interval, so we don't get simultaneous timers
        if (this.autosave_timer) {
            clearInterval(this.autosave_timer);
        }
        if (!this.writable) {
            // disable autosave if not writable
            interval = 0;
        }
        
        this.autosave_interval = this.minimum_autosave_interval = interval;
        if (interval) {
            this.autosave_timer = setInterval(function() {
                if (that.dirty) {
                    that.save_notebook();
                }
            }, interval);
            this.events.trigger("autosave_enabled.Notebook", interval);
        } else {
            this.autosave_timer = null;
            this.events.trigger("autosave_disabled.Notebook");
        }
    };
    
    /**
     * Save this notebook on the server. This becomes a notebook instance's
     * .save_notebook method *after* the entire notebook has been loaded.
     */
    Notebook.prototype.save_notebook = function (check_last_modified) {
        if (check_last_modified === undefined) {
            check_last_modified = true;
        }
        if (!this._fully_loaded) {
            this.events.trigger('notebook_save_failed.Notebook',
                new Error("Load failed, save is disabled")
            );
            return;
        } else if (!this.writable) {
            this.events.trigger('notebook_save_failed.Notebook',
                new Error("Notebook is read-only")
            );
            return;
        }

        // Trigger an event before save, which allows listeners to modify
        // the notebook as needed.
        this.events.trigger('before_save.Notebook');

        // Create a JSON model to be sent to the server.
        var model = {
            type : "notebook",
            content : this.toJSON()
        };
        // time the ajax call for autosave tuning purposes.
        var start =  new Date().getTime();

        var that = this;
        var _save = function () {
            return that.contents.save(that.notebook_path, model).then(
                $.proxy(that.save_notebook_success, that, start),
                function (error) {
                    that.events.trigger('notebook_save_failed.Notebook', error);
                }
            );
        };

        if (check_last_modified) {
            return this.contents.get(this.notebook_path, {content: false}).then(
                function (data) {
                    var last_modified = new Date(data.last_modified);
                    if (last_modified > that.last_modified) {
                        dialog.modal({
                            notebook: that,
                            keyboard_manager: that.keyboard_manager,
                            title: "Notebook changed",
                            body: "Notebook has changed since we opened it. Overwrite the changed file?",
                            buttons: {
                                Cancel: {},
                                Overwrite: {
                                    class: 'btn-danger',
                                    click: function () {
                                        _save();
                                    }
                                },
                            }
                        });
                    } else {
                        return _save();
                    }
                }, function (error) {
                    // maybe it has been deleted or renamed? Go ahead and save.
                    return _save();
                }
            );
        } else {
            return _save();
        }
    };
    
    /**
     * Success callback for saving a notebook.
     * 
     * @param {integer} start - Time when the save request start
     * @param {object}  data - JSON representation of a notebook
     */
    Notebook.prototype.save_notebook_success = function (start, data) {
        this.set_dirty(false);
        this.last_modified = new Date(data.last_modified);
        if (data.message) {
            // save succeeded, but validation failed.
            var body = $("<div>");
            var title = "Notebook validation failed";

            body.append($("<p>").text(
                "The save operation succeeded," +
                " but the notebook does not appear to be valid." +
                " The validation error was:"
            )).append($("<div>").addClass("validation-error").append(
                $("<pre>").text(data.message)
            ));
            dialog.modal({
                notebook: this,
                keyboard_manager: this.keyboard_manager,
                title: title,
                body: body,
                buttons : {
                    OK : {
                        "class" : "btn-primary"
                    }
                }
            });
        }
        this.events.trigger('notebook_saved.Notebook');
        this._update_autosave_interval(start);
        if (this._checkpoint_after_save) {
            this.create_checkpoint();
            this._checkpoint_after_save = false;
        }
    };
    
    /**
     * Update the autosave interval based on the duration of the last save.
     * 
     * @param {integer} timestamp - when the save request started
     */
    Notebook.prototype._update_autosave_interval = function (start) {
        var duration = (new Date().getTime() - start);
        if (this.autosave_interval) {
            // new save interval: higher of 10x save duration or parameter (default 30 seconds)
            var interval = Math.max(10 * duration, this.minimum_autosave_interval);
            // round to 10 seconds, otherwise we will be setting a new interval too often
            interval = 10000 * Math.round(interval / 10000);
            // set new interval, if it's changed
            if (interval !== this.autosave_interval) {
                this.set_autosave_interval(interval);
            }
        }
    };

    /**
     * Explicitly trust the output of this notebook.
     */
    Notebook.prototype.trust_notebook = function () {
        var body = $("<div>").append($("<p>")
            .text("A trusted IPython notebook may execute hidden malicious code ")
            .append($("<strong>")
                .append(
                    $("<em>").text("when you open it")
                )
            ).append(".").append(
                " Selecting trust will immediately reload this notebook in a trusted state."
            ).append(
                " For more information, see the "
            ).append($("<a>").attr("href", "http://ipython.org/ipython-doc/2/notebook/security.html")
                .text("IPython security documentation")
            ).append(".")
        );

        var nb = this;
        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title: "Trust this notebook?",
            body: body,

            buttons: {
                Cancel : {},
                Trust : {
                    class : "btn-danger",
                    click : function () {
                        var cells = nb.get_cells();
                        for (var i = 0; i < cells.length; i++) {
                            var cell = cells[i];
                            if (cell.cell_type === 'code') {
                                cell.output_area.trusted = true;
                            }
                        }
                        nb.events.on('notebook_saved.Notebook', function () {
                            window.location.reload();
                        });
                        nb.save_notebook();
                    }
                }
            }
        });
    };

    /**
     * Make a copy of the current notebook.
     */
    Notebook.prototype.copy_notebook = function () {
        var that = this;
        var base_url = this.base_url;
        var w = window.open('', IPython._target);
        var parent = utils.url_path_split(this.notebook_path)[0];
        this.contents.copy(this.notebook_path, parent).then(
            function (data) {
                w.location = utils.url_join_encode(
                    base_url, 'notebooks', data.path
                );
            },
            function(error) {
                w.close();
                that.events.trigger('notebook_copy_failed', error);
            }
        );
    };
    
    /**
     * Ensure a filename has the right extension
     * Returns the filename with the appropriate extension, appending if necessary.
     */
    Notebook.prototype.ensure_extension = function (name) {
        if (!name.match(/\.ipynb$/)) {
            name = name + ".ipynb";
        }
        return name;
    };

    /**
     * Rename the notebook.
     * @param  {string} new_name
     * @return {Promise} promise that resolves when the notebook is renamed.
     */
    Notebook.prototype.rename = function (new_name) {
        new_name = this.ensure_extension(new_name);

        var that = this;
        var parent = utils.url_path_split(this.notebook_path)[0];
        var new_path = utils.url_path_join(parent, new_name);
        return this.contents.rename(this.notebook_path, new_path).then(
            function (json) {
                that.notebook_name = json.name;
                that.notebook_path = json.path;
                that.last_modified = new Date(json.last_modified);
                that.session.rename_notebook(json.path);
                that.events.trigger('notebook_renamed.Notebook', json);
            }
        );
    };

    /**
     * Delete this notebook
     */
    Notebook.prototype.delete = function () {
        this.contents.delete(this.notebook_path);
    };

    /**
     * Request a notebook's data from the server.
     * 
     * @param {string} notebook_path - A notebook to load
     */
    Notebook.prototype.load_notebook = function (notebook_path) {
        var that = this;
        this.notebook_path = notebook_path;
        this.notebook_name = utils.url_path_split(this.notebook_path)[1];
        this.events.trigger('notebook_loading.Notebook');
        this.contents.get(notebook_path, {type: 'notebook'}).then(
            $.proxy(this.load_notebook_success, this),
            $.proxy(this.load_notebook_error, this)
        );
    };

    /**
     * Success callback for loading a notebook from the server.
     * 
     * Load notebook data from the JSON response.
     * 
     * @param {object} data JSON representation of a notebook
     */
    Notebook.prototype.load_notebook_success = function (data) {
        var failed, msg;
        try {
            this.fromJSON(data);
        } catch (e) {
            failed = e;
            console.log("Notebook failed to load from JSON:", e);
        }
        if (failed || data.message) {
            // *either* fromJSON failed or validation failed
            var body = $("<div>");
            var title;
            if (failed) {
                title = "Notebook failed to load";
                body.append($("<p>").text(
                    "The error was: "
                )).append($("<div>").addClass("js-error").text(
                    failed.toString()
                )).append($("<p>").text(
                    "See the error console for details."
                ));
            } else {
                title = "Notebook validation failed";
            }

            if (data.message) {
                if (failed) {
                    msg = "The notebook also failed validation:";
                } else {
                    msg = "An invalid notebook may not function properly." +
                    " The validation error was:";
                }
                body.append($("<p>").text(
                    msg
                )).append($("<div>").addClass("validation-error").append(
                    $("<pre>").text(data.message)
                ));
            }

            dialog.modal({
                notebook: this,
                keyboard_manager: this.keyboard_manager,
                title: title,
                body: body,
                buttons : {
                    OK : {
                        "class" : "btn-primary"
                    }
                }
            });
        }
        if (this.ncells() === 0) {
            this.insert_cell_below('code');
            this.edit_mode(0);
        } else {
            this.select(0);
            this.handle_command_mode(this.get_cell(0));
        }
        this.set_dirty(false);
        this.scroll_to_top();
        this.writable = data.writable || false;
        this.last_modified = new Date(data.last_modified);
        var nbmodel = data.content;
        var orig_nbformat = nbmodel.metadata.orig_nbformat;
        var orig_nbformat_minor = nbmodel.metadata.orig_nbformat_minor;
        if (orig_nbformat !== undefined && nbmodel.nbformat !== orig_nbformat) {
            var src;
            if (nbmodel.nbformat > orig_nbformat) {
                src = " an older notebook format ";
            } else {
                src = " a newer notebook format ";
            }
            
            msg = "This notebook has been converted from" + src +
            "(v"+orig_nbformat+") to the current notebook " +
            "format (v"+nbmodel.nbformat+"). The next time you save this notebook, the " +
            "current notebook format will be used.";
            
            if (nbmodel.nbformat > orig_nbformat) {
                msg += " Older versions of IPython may not be able to read the new format.";
            } else {
                msg += " Some features of the original notebook may not be available.";
            }
            msg += " To preserve the original version, close the " +
                "notebook without saving it.";
            dialog.modal({
                notebook: this,
                keyboard_manager: this.keyboard_manager,
                title : "Notebook converted",
                body : msg,
                buttons : {
                    OK : {
                        class : "btn-primary"
                    }
                }
            });
        } else if (this.nbformat_minor < nbmodel.nbformat_minor) {
            this.nbformat_minor = nbmodel.nbformat_minor;
        }

        if (this.session === null) {
            var kernel_name = utils.get_url_param('kernel_name');
            if (kernel_name) {
                this.kernel_selector.set_kernel(kernel_name);
            } else if (this.metadata.kernelspec) {
                this.kernel_selector.set_kernel(this.metadata.kernelspec);
            } else if (this.metadata.language) {
                // compat with IJulia, IHaskell, and other early kernels
                // adopters that where setting a language metadata.
                this.kernel_selector.set_kernel({
                    name: "(No name)",
                    language: this.metadata.language
                  });
                // this should be stored in kspec now, delete it.
                // remove once we do not support notebook v3 anymore.
                delete this.metadata.language;
            } else {
                // setting kernel via set_kernel above triggers start_session,
                // otherwise start a new session with the server's default kernel
                // spec_changed events will fire after kernel is loaded
                this.start_session();
            }
        }
        // load our checkpoint list
        this.list_checkpoints();
        
        // load toolbar state
        if (this.metadata.celltoolbar) {
            celltoolbar.CellToolbar.global_show();
            celltoolbar.CellToolbar.activate_preset(this.metadata.celltoolbar);
        } else {
            celltoolbar.CellToolbar.global_hide();
        }
        
        if (!this.writable) {
            this.set_autosave_interval(0);
            this.events.trigger('notebook_read_only.Notebook');
        }
        
        // now that we're fully loaded, it is safe to restore save functionality
        this._fully_loaded = true;
        this.events.trigger('notebook_loaded.Notebook');
    };

    Notebook.prototype.set_kernelselector = function(k_selector){
        this.kernel_selector = k_selector;
    };

    /**
     * Failure callback for loading a notebook from the server.
     * 
     * @param {Error} error
     */
    Notebook.prototype.load_notebook_error = function (error) {
        this.events.trigger('notebook_load_failed.Notebook', error);
        var msg;
        if (error.name === utils.XHR_ERROR && error.xhr.status === 500) {
            utils.log_ajax_error(error.xhr, error.xhr_status, error.xhr_error);
            msg = "An unknown error occurred while loading this notebook. " +
            "This version can load notebook formats " +
            "v" + this.nbformat + " or earlier. See the server log for details.";
        } else {
            msg = error.message;
            console.warn('Error stack trace while loading notebook was:');
            console.warn(error.stack);
        }
        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title: "Error loading notebook",
            body : msg,
            buttons : {
                "OK": {}
            }
        });
    };

    /*********************  checkpoint-related  ********************/
    
    /**
     * Save the notebook then immediately create a checkpoint.
     */
    Notebook.prototype.save_checkpoint = function () {
        this._checkpoint_after_save = true;
        this.save_notebook();
    };
    
    /**
     * Add a checkpoint for this notebook.
     */
    Notebook.prototype.add_checkpoint = function (checkpoint) {
        var found = false;
        for (var i = 0; i < this.checkpoints.length; i++) {
            var existing = this.checkpoints[i];
            if (existing.id === checkpoint.id) {
                found = true;
                this.checkpoints[i] = checkpoint;
                break;
            }
        }
        if (!found) {
            this.checkpoints.push(checkpoint);
        }
        this.last_checkpoint = this.checkpoints[this.checkpoints.length - 1];
    };
    
    /**
     * List checkpoints for this notebook.
     */
    Notebook.prototype.list_checkpoints = function () {
        var that = this;
        this.contents.list_checkpoints(this.notebook_path).then(
            $.proxy(this.list_checkpoints_success, this),
            function(error) {
                that.events.trigger('list_checkpoints_failed.Notebook', error);
            }
        );
    };

    /**
     * Success callback for listing checkpoints.
     * 
     * @param {object} data - JSON representation of a checkpoint
     */
    Notebook.prototype.list_checkpoints_success = function (data) {
        this.checkpoints = data;
        if (data.length) {
            this.last_checkpoint = data[data.length - 1];
        } else {
            this.last_checkpoint = null;
        }
        this.events.trigger('checkpoints_listed.Notebook', [data]);
    };

    /**
     * Create a checkpoint of this notebook on the server from the most recent save.
     */
    Notebook.prototype.create_checkpoint = function () {
        var that = this;
        this.contents.create_checkpoint(this.notebook_path).then(
            $.proxy(this.create_checkpoint_success, this),
            function (error) {
                that.events.trigger('checkpoint_failed.Notebook', error);
            }
        );
    };

    /**
     * Success callback for creating a checkpoint.
     * 
     * @param {object} data - JSON representation of a checkpoint
     */
    Notebook.prototype.create_checkpoint_success = function (data) {
        this.add_checkpoint(data);
        this.events.trigger('checkpoint_created.Notebook', data);
    };

    /**
     * Display the restore checkpoint dialog
     * @param  {string} checkpoint ID
     */
    Notebook.prototype.restore_checkpoint_dialog = function (checkpoint) {
        var that = this;
        checkpoint = checkpoint || this.last_checkpoint;
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
                moment(checkpoint.last_modified).format('LLLL') +
                ' ('+moment(checkpoint.last_modified).fromNow()+')'// Long form:  Tuesday, January 27, 2015 12:15 PM
            ).css("text-align", "center")
        );
        
        dialog.modal({
            notebook: this,
            keyboard_manager: this.keyboard_manager,
            title : "Revert notebook to checkpoint",
            body : body,
            buttons : {
                Revert : {
                    class : "btn-danger",
                    click : function () {
                        that.restore_checkpoint(checkpoint.id);
                    }
                },
                Cancel : {}
                }
        });
    };
    
    /**
     * Restore the notebook to a checkpoint state.
     * 
     * @param {string} checkpoint ID
     */
    Notebook.prototype.restore_checkpoint = function (checkpoint) {
        this.events.trigger('notebook_restoring.Notebook', checkpoint);
        var that = this;
        this.contents.restore_checkpoint(this.notebook_path, checkpoint).then(
            $.proxy(this.restore_checkpoint_success, this),
            function (error) {
                that.events.trigger('checkpoint_restore_failed.Notebook', error);
            }
        );
    };
    
    /**
     * Success callback for restoring a notebook to a checkpoint.
     */
    Notebook.prototype.restore_checkpoint_success = function () {
        this.events.trigger('checkpoint_restored.Notebook');
        this.load_notebook(this.notebook_path);
    };

    /**
     * Delete a notebook checkpoint.
     * 
     * @param {string} checkpoint ID
     */
    Notebook.prototype.delete_checkpoint = function (checkpoint) {
        this.events.trigger('notebook_restoring.Notebook', checkpoint);
        var that = this;
        this.contents.delete_checkpoint(this.notebook_path, checkpoint).then(
            $.proxy(this.delete_checkpoint_success, this),
            function (error) {
                that.events.trigger('checkpoint_delete_failed.Notebook', error);
            }
        );
    };
    
    /**
     * Success callback for deleting a notebook checkpoint.
     */
    Notebook.prototype.delete_checkpoint_success = function () {
        this.events.trigger('checkpoint_deleted.Notebook');
        this.load_notebook(this.notebook_path);
    };


    // For backwards compatability.
    IPython.Notebook = Notebook;

    return {'Notebook': Notebook};
});
