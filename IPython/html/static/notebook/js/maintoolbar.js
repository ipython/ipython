//----------------------------------------------------------------------------
//  Copyright (C) 2011 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ToolBar
//============================================================================

var IPython = (function (IPython) {
    "use strict";

    var MainToolBar = function (selector) {
        IPython.ToolBar.apply(this, arguments);
        this.construct();
        this.add_celltype_list();
        this.add_celltoolbar_list();
        this.bind_events();
    };

    MainToolBar.prototype = new IPython.ToolBar();

    MainToolBar.prototype.construct = function () {

        this.add_buttons_group([
                {
                    id : 'save_b',
                    label : 'Read mode',
                    icon : 'icon-align-right',
                    shortcut : '',
                    callback : function () {
                        IPython.notebook.read_mode_on();
                    }
                }
            ]);

        this.add_buttons_group([
                {
                    id : 'save_b',
                    label : 'Save and Checkpoint',
                    icon : 'icon-save',
                    shortcut : 'Ctrl-s',
                    callback : function () {
                        IPython.notebook.save_checkpoint();
                        }
                }
            ]);

        this.add_buttons_group([
                {
                    id : 'insert_below_b',
                    label : 'Insert Cell Below',
                    icon : 'icon-plus-sign',
                    shortcut : 'Ctrl-m b',
                    callback : function () {
                        IPython.notebook.insert_cell_below('code');
                        IPython.notebook.select_next();
                        IPython.notebook.focus_cell();
                        }
                }
            ],'insert_above_below');

        this.add_buttons_group([
                {
                    id : 'cut_b',
                    label : 'Cut Cell',
                    icon : 'icon-cut',
                    shortcut : 'Ctrl-m x',
                    callback : function () {
                        IPython.notebook.cut_cell();
                        }
                }
            ],'cut_copy_paste');
        this.add_buttons_group([
                {
                    id : 'copy_b',
                    label : 'Copy Cell',
                    icon : 'icon-copy',
                    shortcut : 'Ctrl-m c',
                    callback : function () {
                        IPython.notebook.copy_cell();
                        }
                }
            ],'cut_copy_paste');
        this.add_buttons_group([
                {
                    id : 'paste_b',
                    label : 'Paste Cell Below',
                    icon : 'icon-paste',
                    shortcut : 'Ctrl-m v',
                    callback : function () {
                        IPython.notebook.paste_cell_below();
                        }
                }
            ],'cut_copy_paste');

        this.add_buttons_group([
                {
                    id : 'move_up_b',
                    label : 'Move Cell Up',
                    icon : 'icon-arrow-up',
                    shortcut : 'Ctrl-m k',
                    callback : function () {
                        IPython.notebook.move_cell_up();
                        }
                }
            ],'move_up_down');
        this.add_buttons_group([
                {
                    id : 'move_down_b',
                    label : 'Move Cell Down',
                    icon : 'icon-arrow-down',
                    shortcut : 'Ctrl-m j',
                    callback : function () {
                        IPython.notebook.move_cell_down();
                        }
                }
            ],'move_up_down');


        this.add_buttons_group([
                {
                    id : 'run_b',
                    label : 'Run Cell',
                    icon : 'icon-play',
                    shortcut : 'Shift-Enter',
                    callback : function () {
                        // emulate default shift-enter behavior
                        IPython.notebook.execute_cell_and_select_below();
                    }
                }
            ],'run_int');
        this.add_buttons_group([
                {
                    id : 'interrupt_b',
                    label : 'Interrupt',
                    icon : 'icon-stop',
                    shortcut : 'Ctrl-m i',
                    callback : function () {
                        IPython.notebook.session.interrupt_kernel();
                        }
                }
            ],'run_int');
        this.add_buttons_group([
                {
                    id : 'repeat_b',
                    label : 'Restart Kernel',
                    icon : 'icon-repeat',
                    shortcut : 'Ctrl-m .',
                    callback : function () {
                        IPython.notebook.restart_kernel();
                        }
                }
            ],'run_int');
    };

    MainToolBar.prototype.add_celltype_list = function () {
        $('#cell-type-selector')
            .append($('<select/>')
                .attr('id','cell_type')
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
            .append($('<option/>').attr('value', '').text('None'));
        $('#cell-type-selector')
            .append(select);
        select.change(function() {
                var val = $(this).val()
                if (val =='') {
                    IPython.CellToolbar.global_hide();
                    delete IPython.notebook.metadata.celltoolbar;
                } else {
                    IPython.CellToolbar.global_show();
                    IPython.CellToolbar.activate_preset(val);
                    IPython.notebook.metadata.celltoolbar = val;
                }
            });
        // Setup the currently registered presets.
        var presets = IPython.CellToolbar.list_presets();
        for (var i=0; i<presets.length; i++) {
            var name = presets[i];
            select.append($('<option/>').attr('value', name).text(name));
        }
        // Setup future preset registrations.
        $([IPython.events]).on('preset_added.CellToolbar', function (event, data) {
            var name = data.name;
            select.append($('<option/>').attr('value', name).text(name));
        });
    };


    MainToolBar.prototype.bind_events = function () {
        var that = this;

        $('#cell_type').change(function () {
            var cell_type = $(this).val();
            if (cell_type === 'code') {
                IPython.notebook.to_code();
            } else if (cell_type === 'markdown')  {
                IPython.notebook.to_markdown();
            } else if (cell_type === 'raw')  {
                IPython.notebook.to_raw();
            } else if (cell_type === 'heading1')  {
                IPython.notebook.to_heading(undefined, 1);
            } else if (cell_type === 'heading2')  {
                IPython.notebook.to_heading(undefined, 2);
            } else if (cell_type === 'heading3')  {
                IPython.notebook.to_heading(undefined, 3);
            } else if (cell_type === 'heading4')  {
                IPython.notebook.to_heading(undefined, 4);
            } else if (cell_type === 'heading5')  {
                IPython.notebook.to_heading(undefined, 5);
            } else if (cell_type === 'heading6')  {
                IPython.notebook.to_heading(undefined, 6);
            }
        });
        $([IPython.events]).on('selected_cell_type_changed.Notebook', function (event, data) {
            if (data.cell_type === 'heading') {
                that.element.find('#cell_type').val(data.cell_type+data.level);
            } else {
                that.element.find('#cell_type').val(data.cell_type);
            }
        });
    };

    IPython.MainToolBar = MainToolBar;

    return IPython;

}(IPython));
