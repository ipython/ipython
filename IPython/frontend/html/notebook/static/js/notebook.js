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
        this.control_key_active = false;
        this.notebook_id = null;
        this.notebook_name = null;
        this.notebook_name_blacklist_re = /[\/\\:]/;
        this.nbformat = 3 // Increment this when changing the nbformat
        this.nbformat_minor = 0 // Increment this when changing the nbformat
        this.style();
        this.create_elements();
        this.bind_events();
	this.tabs = IPython.tab_manager.tabs;
    };


    Notebook.prototype.style = function () {
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.create_elements = function () {
        $('div#notebook').addClass('border-box-sizing');
    };


    Notebook.prototype.bind_events = function () {
        var that = this;

        $(document).keydown(function (event) {
	    var current_sheet = that.get_selected_worksheet();

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
                var cell = current_sheet.get_selected_cell();
                if (cell.at_top()) {
                    event.preventDefault();
                    current_sheet.select_prev();
                };
            } else if (event.which === key.DOWNARROW && !event.shiftKey) {
                var cell = current_sheet.get_selected_cell();
                if (cell.at_bottom()) {
                    event.preventDefault();
                    current_sheet.select_next();
                };
            } else if (event.which === key.ENTER && event.shiftKey) {
                current_sheet.execute_selected_cell();
                return false;
            } else if (event.which === key.ENTER && event.ctrlKey) {
                current_sheet.execute_selected_cell({terminal:true});
                return false;
            } else if (event.which === 77 && event.ctrlKey && that.control_key_active == false) {
                that.control_key_active = true;
                return false;
            } else if (event.which === 88 && that.control_key_active) {
                // Cut selected cell = x
                current_sheet.cut_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 67 && that.control_key_active) {
                // Copy selected cell = c
                current_sheet.copy_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 86 && that.control_key_active) {
                // Paste selected cell = v
                current_sheet.paste_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 68 && that.control_key_active) {
                // Delete selected cell = d
                current_sheet.delete_cell();
                that.control_key_active = false;
                return false;
            } else if (event.which === 65 && that.control_key_active) {
                // Insert code cell above selected = a
                current_sheet.insert_cell_above('code');
                that.control_key_active = false;
                return false;
            } else if (event.which === 66 && that.control_key_active) {
                // Insert code cell below selected = b
                current_sheet.insert_cell_below('code');
                that.control_key_active = false;
                return false;
            } else if (event.which === 89 && that.control_key_active) {
                // To code = y
                current_sheet.to_code();
                that.control_key_active = false;
                return false;
            } else if (event.which === 77 && that.control_key_active) {
                // To markdown = m
                current_sheet.to_markdown();
                that.control_key_active = false;
                return false;
            } else if (event.which === 84 && that.control_key_active) {
                // To Raw = t
                current_sheet.to_raw();
                that.control_key_active = false;
                return false;
            } else if (event.which === 49 && that.control_key_active) {
                // To Heading 1 = 1
                current_sheet.to_heading(undefined, 1);
                that.control_key_active = false;
                return false;
            } else if (event.which === 50 && that.control_key_active) {
                // To Heading 2 = 2
                current_sheet.to_heading(undefined, 2);
                that.control_key_active = false;
                return false;
            } else if (event.which === 51 && that.control_key_active) {
                // To Heading 3 = 3
                current_sheet.to_heading(undefined, 3);
                that.control_key_active = false;
                return false;
            } else if (event.which === 52 && that.control_key_active) {
                // To Heading 4 = 4
                current_sheet.to_heading(undefined, 4);
                that.control_key_active = false;
                return false;
            } else if (event.which === 53 && that.control_key_active) {
                // To Heading 5 = 5
                current_sheet.to_heading(undefined, 5);
                that.control_key_active = false;
                return false;
            } else if (event.which === 54 && that.control_key_active) {
                // To Heading 6 = 6
                current_sheet.to_heading(undefined, 6);
                that.control_key_active = false;
                return false;
            } else if (event.which === 79 && that.control_key_active) {
                // Toggle output = o
                if (event.shiftKey){
                    current_sheet.toggle_output_scroll();
                } else {
                    current_sheet.toggle_output();
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
                current_sheet.move_cell_down();
                that.control_key_active = false;
                return false;
            } else if (event.which === 75 && that.control_key_active) {
                // Move cell up = k
                current_sheet.move_cell_up();
                that.control_key_active = false;
                return false;
            } else if (event.which === 80 && that.control_key_active) {
                // Select previous = p
                current_sheet.select_prev();
                that.control_key_active = false;
                return false;
            } else if (event.which === 78 && that.control_key_active) {
                // Select next = n
                current_sheet.select_next();
                that.control_key_active = false;
                return false;
            } else if (event.which === 76 && that.control_key_active) {
                // Toggle line numbers = l
                current_sheet.cell_toggle_line_numbers();
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
	    // determine whether there have been any unsaved changes
	    for (var i=0; i<that.nsheets(); i++) {
		if(that.get_worksheet(i).dirty) {
		    that.dirty = true;
		}
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


    // Worksheet indexing, retrieval, etc.

    Notebook.prototype.get_worksheet_elements = function () {
	return this.tabs.children('div.ui-tabs-panel').not('#tab-add');
    };

    Notebook.prototype.get_worksheet_element = function (index) {
	var result = null;
	var e = this.get_worksheet_elements().eq(index);
	if (e.length !== 0) {
	    result = e;
	}
	return result;
    };

    Notebook.prototype.nsheets = function () {
	return this.get_worksheet_elements().length;
    };

    Notebook.prototype.get_worksheets = function () {
	return this.get_worksheet_elements().toArray().map(function (e) {
	    return $(e).data('worksheet');
	})
    };

    Notebook.prototype.get_worksheet = function (index) {
	var result = null;
	var ws = this.get_worksheet_element(index);
	if (ws !== null) {
	    result = ws.data('worksheet');
	}
	return result;
    };

    Notebook.prototype.find_worksheet_index = function (sheet) {
	var result = null;
	this.get_worksheet_elements().filter(function (index) {
	    if ($(this).data('worksheet') == worksheet) {
		result = index;
	    };
	});
	return result;
    };

    Notebook.prototype.index_or_selected_worksheet = function(index) {
	var i;
	if (index === undefined || index === null) {
	    i = this.get_selected_worksheet_index();
	    if (i === null) {
		i = 0;
	    }
	} else {
	    i = index;
	}
	return i;
    };

    Notebook.prototype.get_selected_worksheet = function () {
	var index = this.get_selected_worksheet_index();
	return this.get_worksheet(index);
    };

    Notebook.prototype.is_valid_worksheet_index = function (index) {
	if (index !== null && index >= 0 && index < this.nsheets()) {
	    return true;
	} else {
	    return false;
	}
    };

    Notebook.prototype.get_selected_worksheet_index = function () {
	return this.tabs.tabs('option','selected');
    };

    Notebook.prototype.rename_worksheet = function (name) {
    }

    // Worksheet selection.

    Notebook.prototype.select = function (index) {
	this.tabs.tabs('select',index);
	return this;
    };


    // Worksheet insertion, deletion.

    Notebook.prototype.delete_worksheet = function (index) {
	index = this.index_or_selected_worksheet(index);
	if (this.is_valid_worksheet_index(index)) {
	    this.tabs.tabs('remove',index);
	    if (index === (this.nsheets())) {
		this.select(index-1);
	    } else {
		this.select(index);
	    }
	    this.dirty = true;
	}
	return this;
    };

    Notebook.prototype.insert_worksheet_below = function (name, index) {
	index = this.index_or_selected_worksheet(index);
	id = 'tab-' + utils.uuid(); // generate random id
	if (this.nsheets() === 0) {
	    index = 0;
	} else {
	    index = index+1;
	}
	this.tabs.tabs('add', '#'+id, name, index); // create tab with specified id, name, and position
	var sheet = new IPython.Worksheet(this.tabs.children('#'+id), name, this.kernel);
	this.select(index);
	this.dirty = true;
	return sheet;
    };

    Notebook.prototype.insert_worksheet_above = function (name, index) {
	index = this.index_or_selected_worksheet(index);
	id = 'tab-' + utils.uuid(); // generate random id
	if (this.nsheets() === 0) {
	    index = 0;
	}
	this.tabs.tabs('add', '#'+id, name, index); // create tab with specified id, name, and position
	var sheet = new IPython.Worksheet(this.tabs.children('#'+id), name, this.kernel);
	this.select(index);
	this.dirty = true;
	return sheet;
    };


    // Kernel related things

    // need to update to set kernel for worksheet instead -DLS

    Notebook.prototype.start_kernel = function () {
        var base_url = $('body').data('baseKernelUrl') + "kernels";
        this.kernel = new IPython.Kernel(base_url);
        this.kernel.start(this.notebook_id);
	var nsheets = this.nsheets();
	for (var i=0; i<nsheets; i++) {
	    var sheet = this.get_worksheet(i);
	    sheet.set_kernel(this.kernel);
	}
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
        var nsheets = this.nsheets();
        for (var i=0; i<nsheets; i++) {
            // Always delete cell 0 as they get renumbered as they are deleted.
            this.delete_worksheet(0);
        };
        // Save the metadata and name.
	if(data.metadata !== undefined) {
            this.metadata = data.metadata;
            this.notebook_name = data.metadata.name;
	}
	nsheets = data.worksheets.length;
	var sheet_data = null;
	var new_sheet = null;
	for (var i=0; i<nsheets; i++) {
	    sheet_data = data.worksheets[i];
	    // fetch the name from the metadata if it exists, otherwise use default 
	    if(sheet_data.metadata !== undefined && sheet_data.metadata.name !== undefined) {
		name = sheet_data.metadata.name;
	    } else {
		name = 'New Tab ' + i;
	    }
	    new_sheet = this.insert_worksheet_below(name);
	    new_sheet.fromJSON(sheet_data);
	}
    };


    Notebook.prototype.toJSON = function () {
	var sheets = this.get_worksheets();
	var nsheets = sheets.length;
	var sheet_array = new Array(nsheets);
	for (var i=0; i<nsheets; i++) {
	    // the tabs are not in order when we call get_worksheets
	    var id = sheets[i].worksheet_id;
	    // get index of worksheet among tabs
	    var j = this.element.find('.ui-tabs-nav').find("a[href!='#tab-add']").index($("a[href=#" + id + "]"));
	    // convert sheet to JSON
	    sheet_array[i] = sheets[j].toJSON();
	};
	var data = {
	    worksheets : sheet_array,
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
	// mark notebook and all worksheets as clean
        this.dirty = false;
	for (var i=0; i<this.nsheets(); i++) {
	    this.get_worksheet(i).dirty = false;
	}
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
        if (this.nsheets() === 0) {
            this.insert_worksheet_below('New Tab');
        };
        this.select(0);
        this.dirty = false;
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

