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
        $('ul#menus').wijmenu();
        $('ul#menus').wijmenu("option", "showDelay", 200);
        $('ul#menus').wijmenu("option", "hideDelay", 200);
        $(".selector").wijmenu("option", "animation", {animated:"fade", duration: 200, easing: null})
    };


    MenuBar.prototype.bind_events = function () {
        //  File
        this.element.find('#new_notebook').click(function () {
            window.open($('body').data('baseProjectUrl')+'new');
        });
        this.element.find('#open_notebook').click(function () {
            window.open($('body').data('baseProjectUrl'));
        });
        this.element.find('#save_notebook').click(function () {
            IPython.save_widget.save_notebook();
        });
        this.element.find('#download_ipynb').click(function () {
            var notebook_id = IPython.save_widget.get_notebook_id();
            var url = $('body').data('baseProjectUrl') + 'notebooks/' +
                      notebook_id + '?format=json';
            window.open(url,'_newtab');
        });
        this.element.find('#download_py').click(function () {
            var notebook_id = IPython.save_widget.get_notebook_id();
            var url = $('body').data('baseProjectUrl') + 'notebooks/' +
                      notebook_id + '?format=py';
            window.open(url,'_newtab');
        });
        this.element.find('button#print_notebook').click(function () {
            IPython.print_widget.print_notebook();
        });
        // Edit
        this.element.find('#delete_cell').click(function () {
            IPython.notebook.delete_cell();
        });
        this.element.find('#move_cell_up').click(function () {
            IPython.notebook.move_cell_up();
        });
        this.element.find('#move_cell_down').click(function () {
            IPython.notebook.move_cell_down();
        });
        // Insert
        this.element.find('#insert_cell_above').click(function () {
            IPython.notebook.insert_code_cell_above();
        });
        this.element.find('#insert_cell_below').click(function () {
            IPython.notebook.insert_code_cell_below();
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
        this.element.find('#toggle_output').click(function () {
            IPython.notebook.toggle_output();
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
    };


    IPython.MenuBar = MenuBar;

    return IPython;

}(IPython));
