//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MenuBar
//============================================================================

var IPython = (function (IPython) {

    var MenuBar = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    MenuBar.prototype.style = function () {
        this.element.addClass('border-box-sizing');
        $('ul#menus').menubar({
            select : function (event, ui) {
                // The selected cell loses focus when the menu is entered, so we
                // re-select it upon selection.
                var i = IPython.notebook.get_selected_index();
                IPython.notebook.select(i);
            }
        });
    };


    MenuBar.prototype.bind_events = function () {
        //  File
        this.element.find('#new_notebook').click(function () {
            window.open($('body').data('baseProjectUrl')+'new');
        });
        this.element.find('#open_notebook').click(function () {
            window.open($('body').data('baseProjectUrl'));
        });
        this.element.find('#rename_notebook').click(function () {
            IPython.save_widget.rename_notebook();
        });
        this.element.find('#copy_notebook').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = $('body').data('baseProjectUrl') + notebook_id + '/copy';
            window.open(url,'_newtab');
        });
        this.element.find('#save_notebook').click(function () {
            IPython.notebook.save_notebook();
        });
        this.element.find('#download_ipynb').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = $('body').data('baseProjectUrl') + 'notebooks/' +
                      notebook_id + '?format=json';
            window.open(url,'_newtab');
        });
        this.element.find('#download_py').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = $('body').data('baseProjectUrl') + 'notebooks/' +
                      notebook_id + '?format=py';
            window.open(url,'_newtab');
        });
        this.element.find('button#print_notebook').click(function () {
            IPython.print_widget.print_notebook();
        });
        this.element.find('#kill_and_exit').click(function () {
            IPython.notebook.kernel.kill();
            setTimeout(function(){window.close();}, 200);
        });
        // Edit
        this.element.find('#cut_cell').click(function () {
            IPython.notebook.cut_cell();
        });
        this.element.find('#copy_cell').click(function () {
            IPython.notebook.copy_cell();
        });
        this.element.find('#delete_cell').click(function () {
            IPython.notebook.delete_cell();
        });
        this.element.find('#split_cell').click(function () {
            IPython.notebook.split_cell();
        });
        this.element.find('#merge_cell_above').click(function () {
            IPython.notebook.merge_cell_above();
        });
        this.element.find('#merge_cell_below').click(function () {
            IPython.notebook.merge_cell_below();
        });
        this.element.find('#move_cell_up').click(function () {
            IPython.notebook.move_cell_up();
        });
        this.element.find('#move_cell_down').click(function () {
            IPython.notebook.move_cell_down();
        });
        this.element.find('#select_previous').click(function () {
            IPython.notebook.select_prev();
        });
        this.element.find('#select_next').click(function () {
            IPython.notebook.select_next();
        });
        // View
        this.element.find('#toggle_header').click(function () {
            $('div#header').toggle();
            IPython.layout_manager.do_resize();
        });
        this.element.find('#toggle_toolbar').click(function () {
            IPython.toolbar.toggle();
        });
        // Insert
        this.element.find('#insert_cell_above').click(function () {
            IPython.notebook.insert_cell_above('code');
        });
        this.element.find('#insert_cell_below').click(function () {
            IPython.notebook.insert_cell_below('code');
        });
        // Cell
        this.element.find('#run_cell').click(function () {
            IPython.notebook.execute_selected_cell();
        });
        this.element.find('#run_cell_in_place').click(function () {
            IPython.notebook.execute_selected_cell({terminal:true});
        });
        this.element.find('#run_all_cells').click(function () {
            IPython.notebook.execute_all_cells();
        });
        this.element.find('#to_code').click(function () {
            IPython.notebook.to_code();
        });
        this.element.find('#to_markdown').click(function () {
            IPython.notebook.to_markdown();
        });
        this.element.find('#to_raw').click(function () {
            IPython.notebook.to_raw();
        });
        this.element.find('#to_heading1').click(function () {
            IPython.notebook.to_heading(undefined, 1);
        });
        this.element.find('#to_heading2').click(function () {
            IPython.notebook.to_heading(undefined, 2);
        });
        this.element.find('#to_heading3').click(function () {
            IPython.notebook.to_heading(undefined, 3);
        });
        this.element.find('#to_heading4').click(function () {
            IPython.notebook.to_heading(undefined, 4);
        });
        this.element.find('#to_heading5').click(function () {
            IPython.notebook.to_heading(undefined, 5);
        });
        this.element.find('#to_heading6').click(function () {
            IPython.notebook.to_heading(undefined, 6);
        });
        this.element.find('#toggle_output').click(function () {
            IPython.notebook.toggle_output();
        });
        this.element.find('#collapse_all_output').click(function () {
            IPython.notebook.collapse_all_output();
        });
        this.element.find('#scroll_all_output').click(function () {
            IPython.notebook.scroll_all_output();
        });
        this.element.find('#expand_all_output').click(function () {
            IPython.notebook.expand_all_output();
        });
        this.element.find('#clear_all_output').click(function () {
            IPython.notebook.clear_all_output();
        });
        // Kernel
        this.element.find('#int_kernel').click(function () {
            IPython.notebook.kernel.interrupt();
        });
        this.element.find('#restart_kernel').click(function () {
            IPython.notebook.restart_kernel();
        });
        // Help
        this.element.find('#keyboard_shortcuts').click(function () {
            IPython.quick_help.show_keyboard_shortcuts();
        });
    };


    IPython.MenuBar = MenuBar;

    return IPython;

}(IPython));
