//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MenuBar
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 * @submodule MenuBar
 */


var IPython = (function (IPython) {

    /**
     * A MenuBar Class to generate the menubar of IPython noteboko
     * @Class MenuBar
     *
     * @constructor
     *
     *
     * @param selector {string} selector for the menubar element in DOM
     * @param {object} [options]
     *      @param [options.baseProjectUrl] {String} String to use for the
     *      Base Project url, default would be to inspect
     *      $('body').data('baseProjectUrl');
     *      does not support change for now is set through this option
     */
    var MenuBar = function (selector, options) {
        var options = options || {};
        if(options.baseProjectUrl!= undefined){
            this._baseProjectUrl = options.baseProjectUrl;
        }
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    MenuBar.prototype.baseProjectUrl = function(){
        return this._baseProjectUrl || $('body').data('baseProjectUrl');
    };


    MenuBar.prototype.style = function () {
        this.element.addClass('border-box-sizing');
        this.element.find("li").click(function (event, ui) {
                // The selected cell loses focus when the menu is entered, so we
                // re-select it upon selection.
                var i = IPython.notebook.get_selected_index();
                IPython.notebook.select(i);
            }
        );
    };


    MenuBar.prototype.bind_events = function () {
        //  File
        var that = this;
        this.element.find('#new_notebook').click(function () {
            window.open(that.baseProjectUrl()+'new');
        });
        this.element.find('#open_notebook').click(function () {
            window.open(that.baseProjectUrl());
        });
        this.element.find('#rename_notebook').click(function () {
            IPython.save_widget.rename_notebook();
        });
        this.element.find('#copy_notebook').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = that.baseProjectUrl() + notebook_id + '/copy';
            window.open(url,'_blank');
            return false;
        });
        this.element.find('#save_checkpoint').click(function () {
            IPython.notebook.save_checkpoint();
        });
        this.element.find('#restore_checkpoint').click(function () {
        });
        this.element.find('#download_ipynb').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = that.baseProjectUrl() + 'notebooks/' +
                      notebook_id + '?format=json';
            window.location.assign(url);
        });
        this.element.find('#download_py').click(function () {
            var notebook_id = IPython.notebook.get_notebook_id();
            var url = that.baseProjectUrl() + 'notebooks/' +
                      notebook_id + '?format=py';
            window.location.assign(url);
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
        this.element.find('#undelete_cell').click(function () {
            IPython.notebook.undelete();
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
            $('div#maintoolbar').toggle();
            IPython.layout_manager.do_resize();
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
        }).attr('title', 'Run all cells in the notebook');
        this.element.find('#run_all_cells_above').click(function () {
            IPython.notebook.execute_cells_above();
        }).attr('title', 'Run all cells above (but not including) this cell');
        this.element.find('#run_all_cells_below').click(function () {
            IPython.notebook.execute_cells_below();
        }).attr('title', 'Run this cell and all cells below it');
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
        
        this.update_restore_checkpoint(null);
        
        $([IPython.events]).on('checkpoints_listed.Notebook', function (event, data) {
            that.update_restore_checkpoint(IPython.notebook.checkpoints);
        });
        
        $([IPython.events]).on('checkpoint_created.Notebook', function (event, data) {
            that.update_restore_checkpoint(IPython.notebook.checkpoints);
        });
    };

    MenuBar.prototype.update_restore_checkpoint = function(checkpoints) {
        var ul = this.element.find("#restore_checkpoint").find("ul");
        ul.empty();
        if (! checkpoints || checkpoints.length == 0) {
            ul.append(
                $("<li/>")
                .addClass("disabled")
                .append(
                    $("<a/>")
                    .text("No checkpoints")
                )
            );
            return;
        };
        
        checkpoints.map(function (checkpoint) {
            var d = new Date(checkpoint.last_modified);
            ul.append(
                $("<li/>").append(
                    $("<a/>")
                    .attr("href", "#")
                    .text(d.format("mmm dd HH:MM:ss"))
                    .click(function () {
                        IPython.notebook.restore_checkpoint_dialog(checkpoint);
                    })
                )
            );
        });
    };

    IPython.MenuBar = MenuBar;

    return IPython;

}(IPython));
