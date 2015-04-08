// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'require',
    'base/js/namespace',
    'jquery',
    './toolbar',
    './celltoolbar'
], function(require, IPython, $, toolbar, celltoolbar) {
    "use strict";

    var MainToolBar = function (selector, options) {
        /**
         * Constructor
         *
         * Parameters:
         *  selector: string
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          events: $(Events) instance
         *          notebook: Notebook instance
         **/
        toolbar.ToolBar.apply(this, [selector, options] );
        this.events = options.events;
        this.notebook = options.notebook;
        this._make();
        Object.seal(this);
    };

    MainToolBar.prototype = Object.create(toolbar.ToolBar.prototype);

    MainToolBar.prototype._make = function () {
        var grps = [
          [
            ['ipython.save-notebook'],
            'save-notbook'
          ],
          [
            ['ipython.insert-cell-after'],
            'insert_above_below'],
          [
            ['ipython.cut-selected-cell',
             'ipython.copy-selected-cell',
             'ipython.paste-cell-after'
            ] ,
            'cut_copy_paste'],
          [
            ['ipython.move-selected-cell-up',
             'ipython.move-selected-cell-down'
            ],
            'move_up_down'],
          [ ['ipython.run-select-next',
             'ipython.interrupt-kernel',
             'ipython.restart-kernel'
            ],
            'run_int'],
         ['<add_celltype_list>'],
         ['<add_celltoolbar_list>']
        ];
        this.construct(grps);
    };
    
    // add a cell type drop down to the maintoolbar.
    // triggered when the pseudo action `<add_celltype_list>` is
    // encountered when building a toolbar.
    MainToolBar.prototype._pseudo_actions.add_celltype_list = function () {
        var that = this;
        var sel = $('<select/>')
            .attr('id','cell_type')
            .addClass('form-control select-xs')
            .append($('<option/>').attr('value','code').text('Code'))
            .append($('<option/>').attr('value','markdown').text('Markdown'))
            .append($('<option/>').attr('value','raw').text('Raw NBConvert'))
            .append($('<option/>').attr('value','heading').text('Heading'));
        this.notebook.keyboard_manager.register_events(sel);
        this.events.on('selected_cell_type_changed.Notebook', function (event, data) {
            if (data.cell_type === 'heading') {
                sel.val('Markdown');
            } else {
                sel.val(data.cell_type);
            }
        });
        sel.change(function () {
            var cell_type = $(this).val();
            switch (cell_type) {
            case 'code':
                that.notebook.to_code();
                break;
            case 'markdown':
                that.notebook.to_markdown();
                break;
            case 'raw':
                that.notebook.to_raw();
                break;
            case 'heading':
                that.notebook._warn_heading();
                that.notebook.to_heading();
                sel.val('markdown');
                break;
            default:
                console.log("unrecognized cell type:", cell_type);
            }
            that.notebook.focus_cell();
        });
        return sel;

    };

    MainToolBar.prototype._pseudo_actions.add_celltoolbar_list = function () {
        var label = $('<span/>').addClass("navbar-text").text('Cell Toolbar:');
        var select = $('<select/>')
            .attr('id', 'ctb_select')
            .addClass('form-control select-xs')
            .append($('<option/>').attr('value', '').text('None'));
        var that = this;
        select.change(function() {
                var val = $(this).val();
                if (val ==='') {
                    celltoolbar.CellToolbar.global_hide();
                    delete that.notebook.metadata.celltoolbar;
                } else {
                    celltoolbar.CellToolbar.global_show();
                    celltoolbar.CellToolbar.activate_preset(val, that.events);
                    that.notebook.metadata.celltoolbar = val;
                }
                that.notebook.focus_cell();
            });
        this.notebook.keyboard_manager.register_events(select);
        // Setup the currently registered presets.
        var presets = celltoolbar.CellToolbar.list_presets();
        for (var i=0; i<presets.length; i++) {
            var name = presets[i];
            select.append($('<option/>').attr('value', name).text(name));
        }
        // Setup future preset registrations.
        this.events.on('preset_added.CellToolbar', function (event, data) {
            var name = data.name;
            select.append($('<option/>').attr('value', name).text(name));
        });
        this.events.on('unregistered_preset.CellToolbar', function (event, data) {
            if (select.val() === data.name){
                select.val('');
                celltoolbar.CellToolbar.global_hide();
                delete that.notebook.metadata.celltoolbar;
            }
            select.find("option[value='"+name+"']" ).remove();
        });
        // Update select value when a preset is activated.
        this.events.on('preset_activated.CellToolbar', function (event, data) {
            if (select.val() !== data.name){
                select.val(data.name);
            }
        });

        var wrapper = $('<div/>').addClass('btn-group');
        wrapper.append(label).append(select);
        return wrapper;
    };

    // Backwards compatibility.
    IPython.MainToolBar = MainToolBar;

    return {'MainToolBar': MainToolBar};
});
