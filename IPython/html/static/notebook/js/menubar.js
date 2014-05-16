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
    "use strict";
    
    var utils = IPython.utils;

    /**
     * A MenuBar Class to generate the menubar of IPython notebook
     * @Class MenuBar
     *
     * @constructor
     *
     *
     * @param selector {string} selector for the menubar element in DOM
     * @param {object} [options]
     *      @param [options.base_url] {String} String to use for the
     *      base project url. Default is to inspect
     *      $('body').data('baseUrl');
     *      does not support change for now is set through this option
     */
    var MenuBar = function (selector, options) {
        options = options || {};
        this.base_url = options.base_url || IPython.utils.get_body_data("baseUrl");
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
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

    MenuBar.prototype._nbconvert = function (format, download) {
        download = download || false;
        var notebook_path = IPython.notebook.notebook_path;
        var notebook_name = IPython.notebook.notebook_name;
        if (IPython.notebook.dirty) {
            IPython.notebook.save_notebook({async : false});
        }
        var url = utils.url_join_encode(
            this.base_url,
            'nbconvert',
            format,
            notebook_path,
            notebook_name
        ) + "?download=" + download.toString();

        window.open(url);
    };

    MenuBar.prototype.bind_events = function () {
        //  File
        var that = this;
        this.element.find('#new_notebook').click(function () {
            IPython.notebook.new_notebook();
        });
        this.element.find('#open_notebook').click(function () {
            window.open(utils.url_join_encode(
                IPython.notebook.base_url,
                'tree',
                IPython.notebook.notebook_path
            ));
        });
        this.element.find('#copy_notebook').click(function () {
            IPython.notebook.copy_notebook();
            return false;
        });
        this.element.find('#download_ipynb').click(function () {
            var base_url = IPython.notebook.base_url;
            var notebook_path = IPython.notebook.notebook_path;
            var notebook_name = IPython.notebook.notebook_name;
            if (IPython.notebook.dirty) {
                IPython.notebook.save_notebook({async : false});
            }
            
            var url = utils.url_join_encode(
                base_url,
                'files',
                notebook_path,
                notebook_name
            );
            window.location.assign(url);
        });
        
        this.element.find('#print_preview').click(function () {
            that._nbconvert('html', false);
        });

        this.element.find('#download_py').click(function () {
            that._nbconvert('python', true);
        });

        this.element.find('#download_html').click(function () {
            that._nbconvert('html', true);
        });

        this.element.find('#download_rst').click(function () {
            that._nbconvert('rst', true);
        });

        this.element.find('#rename_notebook').click(function () {
            IPython.save_widget.rename_notebook();
        });
        this.element.find('#save_checkpoint').click(function () {
            IPython.notebook.save_checkpoint();
        });
        this.element.find('#restore_checkpoint').click(function () {
        });
        this.element.find('#trust_notebook').click(function () {
            IPython.notebook.trust_notebook();
        });
        $([IPython.events]).on('trust_changed.Notebook', function (event, trusted) {
            if (trusted) {
                that.element.find('#trust_notebook')
                    .addClass("disabled")
                    .find("a").text("Trusted Notebook");
            } else {
                that.element.find('#trust_notebook')
                    .removeClass("disabled")
                    .find("a").text("Trust Notebook");
            }
        });
        this.element.find('#kill_and_exit').click(function () {
            IPython.notebook.session.delete();
            setTimeout(function(){
                // allow closing of new tabs in Chromium, impossible in FF
                window.open('', '_self', '');
                window.close();
            }, 500);
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
            IPython.notebook.undelete_cell();
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
        this.element.find('#edit_nb_metadata').click(function () {
            IPython.notebook.edit_metadata();
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
            IPython.notebook.select_prev();
        });
        this.element.find('#insert_cell_below').click(function () {
            IPython.notebook.insert_cell_below('code');
            IPython.notebook.select_next();
        });
        // Cell
        this.element.find('#run_cell').click(function () {
            IPython.notebook.execute_cell();
        });
        this.element.find('#run_cell_select_below').click(function () {
            IPython.notebook.execute_cell_and_select_below();
        });
        this.element.find('#run_cell_insert_below').click(function () {
            IPython.notebook.execute_cell_and_insert_below();
        });
        this.element.find('#run_all_cells').click(function () {
            IPython.notebook.execute_all_cells();
        });
        this.element.find('#run_all_cells_above').click(function () {
            IPython.notebook.execute_cells_above();
        });
        this.element.find('#run_all_cells_below').click(function () {
            IPython.notebook.execute_cells_below();
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
        
        this.element.find('#toggle_current_output').click(function () {
            IPython.notebook.toggle_output();
        });
        this.element.find('#toggle_current_output_scroll').click(function () {
            IPython.notebook.toggle_output_scroll();
        });
        this.element.find('#clear_current_output').click(function () {
            IPython.notebook.clear_output();
        });
        
        this.element.find('#toggle_all_output').click(function () {
            IPython.notebook.toggle_all_output();
        });
        this.element.find('#toggle_all_output_scroll').click(function () {
            IPython.notebook.toggle_all_output_scroll();
        });
        this.element.find('#clear_all_output').click(function () {
            IPython.notebook.clear_all_output();
        });
        
        // Kernel
        this.element.find('#int_kernel').click(function () {
            IPython.notebook.session.interrupt_kernel();
        });
        this.element.find('#restart_kernel').click(function () {
            IPython.notebook.restart_kernel();
        });
        // Help
        if (IPython.tour) {
            this.element.find('#notebook_tour').click(function () {
                IPython.tour.start();
            });
        } else {
            this.element.find('#notebook_tour').addClass("disabled");
        }
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
        if (!checkpoints || checkpoints.length === 0) {
            ul.append(
                $("<li/>")
                .addClass("disabled")
                .append(
                    $("<a/>")
                    .text("No checkpoints")
                )
            );
            return;
        }
        
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
