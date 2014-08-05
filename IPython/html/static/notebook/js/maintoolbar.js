// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'notebook/js/toolbar',
    'notebook/js/celltoolbar',
], function(IPython, $, toolbar, celltoolbar) {
    "use strict";

    var MainToolBar = function (selector, options) {
        // Constructor
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance
        //          notebook: Notebook instance
        toolbar.ToolBar.apply(this, arguments);
        this.events = options.events;
        this.notebook = options.notebook;
        this.construct();
        this.add_celltype_list();
        this.add_celltoolbar_list();
        this.bind_events();
    };

    MainToolBar.prototype = new toolbar.ToolBar();

    MainToolBar.prototype.construct = function () {
        var that = this;
        this.add_buttons_group([
                {
                    id : 'save_b',
                    label : 'Save and Checkpoint',
                    icon : 'fa-save',
                    callback : function () {
                        that.notebook.save_checkpoint();
                        }
                }
            ]);

        this.add_buttons_group([
                {
                    id : 'insert_below_b',
                    label : 'Insert Cell Below',
                    icon : 'fa-plus',
                    callback : function () {
                        that.notebook.insert_cell_below('code');
                        that.notebook.select_next();
                        that.notebook.focus_cell();
                        }
                }
            ],'insert_above_below');

        this.add_buttons_group([
                {
                    id : 'cut_b',
                    label : 'Cut Cell',
                    icon : 'fa-cut',
                    callback : function () {
                        that.notebook.cut_cell();
                        }
                },
                {
                    id : 'copy_b',
                    label : 'Copy Cell',
                    icon : 'fa-copy',
                    callback : function () {
                        that.notebook.copy_cell();
                        }
                },
                {
                    id : 'paste_b',
                    label : 'Paste Cell Below',
                    icon : 'fa-paste',
                    callback : function () {
                        that.notebook.paste_cell_below();
                        }
                }
            ],'cut_copy_paste');

        this.add_buttons_group([
                {
                    id : 'move_up_b',
                    label : 'Move Cell Up',
                    icon : 'fa-arrow-up',
                    callback : function () {
                        that.notebook.move_cell_up();
                        }
                },
                {
                    id : 'move_down_b',
                    label : 'Move Cell Down',
                    icon : 'fa-arrow-down',
                    callback : function () {
                        that.notebook.move_cell_down();
                        }
                }
            ],'move_up_down');
        

        this.add_buttons_group([
                {
                    id : 'run_b',
                    label : 'Run Cell',
                    icon : 'fa-play',
                    callback : function () {
                        // emulate default shift-enter behavior
                        that.notebook.execute_cell_and_select_below();
                    }
                },
                {
                    id : 'interrupt_b',
                    label : 'Interrupt',
                    icon : 'fa-stop',
                    callback : function () {
                        that.notebook.session.interrupt_kernel();
                        }
                },
                {
                    id : 'repeat_b',
                    label : 'Restart Kernel',
                    icon : 'fa-repeat',
                    callback : function () {
                        that.notebook.restart_kernel();
                        }
                }
            ],'run_int');
    };
    
    MainToolBar.prototype.add_celltype_list = function () {
        this.element
            .append($('<select/>')
                .attr('id','cell_type')
                .addClass('form-control select-xs')
                // .addClass('ui-widget-content')
                .append($('<option/>').attr('value','code').text('Code'))
                .append($('<option/>').attr('value','markdown').text('Markdown'))
                .append($('<option/>').attr('value','raw').text('Raw NBConvert'))
                .append($('<option/>').attr('value','heading1').text('Heading 1'))
                .append($('<option/>').attr('value','heading2').text('Heading 2'))
                .append($('<option/>').attr('value','heading3').text('Heading 3'))
                .append($('<option/>').attr('value','heading4').text('Heading 4'))
                .append($('<option/>').attr('value','heading5').text('Heading 5'))
                .append($('<option/>').attr('value','heading6').text('Heading 6'))
            );
    };


    MainToolBar.prototype.add_celltoolbar_list = function () {
        var label = $('<span/>').addClass("navbar-text").text('Cell Toolbar:');
        var select = $('<select/>')
            // .addClass('ui-widget-content')
            .attr('id', 'ctb_select')
            .addClass('form-control select-xs')
            .append($('<option/>').attr('value', '').text('None'));
        this.element.append(label).append(select);
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
            });
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
        // Update select value when a preset is activated.
        this.events.on('preset_activated.CellToolbar', function (event, data) {
            if (select.val() !== data.name)
                select.val(data.name);
        });
    };


    MainToolBar.prototype.bind_events = function () {
        var that = this;
        
        this.element.find('#cell_type').change(function () {
            var cell_type = $(this).val();
            if (cell_type === 'code') {
                that.notebook.to_code();
            } else if (cell_type === 'markdown')  {
                that.notebook.to_markdown();
            } else if (cell_type === 'raw')  {
                that.notebook.to_raw();
            } else if (cell_type === 'heading1')  {
                that.notebook.to_heading(undefined, 1);
            } else if (cell_type === 'heading2')  {
                that.notebook.to_heading(undefined, 2);
            } else if (cell_type === 'heading3')  {
                that.notebook.to_heading(undefined, 3);
            } else if (cell_type === 'heading4')  {
                that.notebook.to_heading(undefined, 4);
            } else if (cell_type === 'heading5')  {
                that.notebook.to_heading(undefined, 5);
            } else if (cell_type === 'heading6')  {
                that.notebook.to_heading(undefined, 6);
            }
        });
        this.events.on('selected_cell_type_changed.Notebook', function (event, data) {
            if (data.cell_type === 'heading') {
                that.element.find('#cell_type').val(data.cell_type+data.level);
            } else {
                that.element.find('#cell_type').val(data.cell_type);
            }
        });
    };

    // Backwards compatability.
    IPython.MainToolBar = MainToolBar;

    return {'MainToolBar': MainToolBar};
});
