// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/namespace',
    'base/js/dialog',
    'base/js/utils',
    'notebook/js/tour',
    'bootstrap',
    'moment',
], function($, IPython, dialog, utils, tour, bootstrap, moment) {
    "use strict";
    
    var MenuBar = function (selector, options) {
        /**
         * Constructor
         *
         * A MenuBar Class to generate the menubar of IPython notebook
         *
         * Parameters:
         *  selector: string
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          notebook: Notebook instance
         *          contents: ContentManager instance
         *          events: $(Events) instance
         *          save_widget: SaveWidget instance
         *          quick_help: QuickHelp instance
         *          base_url : string
         *          notebook_path : string
         *          notebook_name : string
         */
        options = options || {};
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.selector = selector;
        this.notebook = options.notebook;
        this.contents = options.contents;
        this.events = options.events;
        this.save_widget = options.save_widget;
        this.quick_help = options.quick_help;

        try {
            this.tour = new tour.Tour(this.notebook, this.events);
        } catch (e) {
            this.tour = undefined;
            console.log("Failed to instantiate Notebook Tour", e);
        }

        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    // TODO: This has definitively nothing to do with style ...
    MenuBar.prototype.style = function () {
        var that = this;
        this.element.find("li").click(function (event, ui) {
                // The selected cell loses focus when the menu is entered, so we
                // re-select it upon selection.
                var i = that.notebook.get_selected_index();
                that.notebook.select(i);
            }
        );
    };

    MenuBar.prototype._nbconvert = function (format, download) {
        download = download || false;
        var notebook_path = this.notebook.notebook_path;
        var url = utils.url_join_encode(
            this.base_url,
            'nbconvert',
            format,
            notebook_path
        ) + "?download=" + download.toString();
        
        var w = window.open('', IPython._target);
        if (this.notebook.dirty) {
            this.notebook.save_notebook().then(function() {
                w.location = url;
            });
        } else {
            w.location = url;
        }
    };

    MenuBar.prototype._size_header = function() {
        /** 
         * Update header spacer size.
         */
        this.events.trigger('resize-header.Page');
    };

    MenuBar.prototype.bind_events = function () {
        /**
         *  File
         */
        var that = this;
        
        this.element.find('#open_notebook').click(function () {
            var parent = utils.url_path_split(that.notebook.notebook_path)[0];
            window.open(utils.url_join_encode(that.base_url, 'tree', parent), IPython._target);
        });
        this.element.find('#copy_notebook').click(function () {
            if (that.notebook.dirty) {
                that.notebook.save_notebook({async : false});
            }
            that.notebook.copy_notebook();
            return false;
        });
        this.element.find('#download_ipynb').click(function () {
            var base_url = that.notebook.base_url;
            var notebook_path = that.notebook.notebook_path;
            if (that.notebook.dirty) {
                that.notebook.save_notebook({async : false});
            }
            
            var url = utils.url_join_encode(base_url, 'files', notebook_path);
            window.open(url + '?download=1');
        });
        
        this.element.find('#print_preview').click(function () {
            that._nbconvert('html', false);
        });

        this.element.find('#download_html').click(function () {
            that._nbconvert('html', true);
        });

        this.element.find('#download_markdown').click(function () {
            that._nbconvert('markdown', true);
        });

        this.element.find('#download_rst').click(function () {
            that._nbconvert('rst', true);
        });

        this.element.find('#download_pdf').click(function () {
            that._nbconvert('pdf', true);
        });

        this.element.find('#download_script').click(function () {
            that._nbconvert('script', true);
        });

        this.element.find('#rename_notebook').click(function () {
            that.save_widget.rename_notebook({notebook: that.notebook});
        });

        this.element.find('#save_checkpoint').click(function () {
            that.notebook.save_checkpoint();
        });

        this.element.find('#restore_checkpoint').click(function () {
        });

        this.element.find('#trust_notebook').click(function () {
            that.notebook.trust_notebook();
        });
        this.events.on('trust_changed.Notebook', function (event, trusted) {
            if (trusted) {
                that.element.find('#trust_notebook')
                    .addClass("disabled").off('click')
                    .find("a").text("Trusted Notebook");
            } else {
                that.element.find('#trust_notebook')
                    .removeClass("disabled").on('click', function () {
                        that.notebook.trust_notebook();
                    })
                    .find("a").text("Trust Notebook");
            }
        });

        this.element.find('#kill_and_exit').click(function () {
            var close_window = function () {
                /**
                 * allow closing of new tabs in Chromium, impossible in FF
                 */
                window.open('', '_self', '');
                window.close();
            };
            // finish with close on success or failure
            that.notebook.session.delete(close_window, close_window);
        });

        // Edit
        this.element.find('#cut_cell').click(function () {
            that.notebook.cut_cell();
        });
        this.element.find('#copy_cell').click(function () {
            that.notebook.copy_cell();
        });
        this.element.find('#delete_cell').click(function () {
            that.notebook.delete_cell();
        });
        this.element.find('#undelete_cell').click(function () {
            that.notebook.undelete_cell();
        });
        this.element.find('#split_cell').click(function () {
            that.notebook.split_cell();
        });
        this.element.find('#merge_cell_above').click(function () {
            that.notebook.merge_cell_above();
        });
        this.element.find('#merge_cell_below').click(function () {
            that.notebook.merge_cell_below();
        });
        this.element.find('#move_cell_up').click(function () {
            that.notebook.move_cell_up();
        });
        this.element.find('#move_cell_down').click(function () {
            that.notebook.move_cell_down();
        });
        this.element.find('#edit_nb_metadata').click(function () {
            that.notebook.edit_metadata({
                notebook: that.notebook,
                keyboard_manager: that.notebook.keyboard_manager});
        });
        
        // View
        this.element.find('#toggle_header').click(function () {
            $('#header-container').toggle();
            $('.header-bar').toggle();
            that._size_header();
        });
        this.element.find('#toggle_toolbar').click(function () {
            $('div#maintoolbar').toggle();
            that._size_header();
        });
        // Insert
        this.element.find('#insert_cell_above').click(function () {
            that.notebook.insert_cell_above('code');
            that.notebook.select_prev();
        });
        this.element.find('#insert_cell_below').click(function () {
            that.notebook.insert_cell_below('code');
            that.notebook.select_next();
        });
        // Cell
        this.element.find('#run_cell').click(function () {
            that.notebook.execute_cell();
        });
        this.element.find('#run_cell_select_below').click(function () {
            that.notebook.execute_cell_and_select_below();
        });
        this.element.find('#run_cell_insert_below').click(function () {
            that.notebook.execute_cell_and_insert_below();
        });
        this.element.find('#run_all_cells').click(function () {
            that.notebook.execute_all_cells();
        });
        this.element.find('#run_all_cells_above').click(function () {
            that.notebook.execute_cells_above();
        });
        this.element.find('#run_all_cells_below').click(function () {
            that.notebook.execute_cells_below();
        });
        this.element.find('#to_code').click(function () {
            that.notebook.to_code();
        });
        this.element.find('#to_markdown').click(function () {
            that.notebook.to_markdown();
        });
        this.element.find('#to_raw').click(function () {
            that.notebook.to_raw();
        });
        
        this.element.find('#toggle_current_output').click(function () {
            that.notebook.toggle_output();
        });
        this.element.find('#toggle_current_output_scroll').click(function () {
            that.notebook.toggle_output_scroll();
        });
        this.element.find('#clear_current_output').click(function () {
            that.notebook.clear_output();
        });
        
        this.element.find('#toggle_all_output').click(function () {
            that.notebook.toggle_all_output();
        });
        this.element.find('#toggle_all_output_scroll').click(function () {
            that.notebook.toggle_all_output_scroll();
        });
        this.element.find('#clear_all_output').click(function () {
            that.notebook.clear_all_output();
        });
        
        // Kernel
        this.element.find('#int_kernel').click(function () {
            that.notebook.kernel.interrupt();
        });
        this.element.find('#restart_kernel').click(function () {
            that.notebook.restart_kernel();
        });
        this.element.find('#reconnect_kernel').click(function () {
            that.notebook.kernel.reconnect();
        });
        // Help
        if (this.tour) {
            this.element.find('#notebook_tour').click(function () {
                that.tour.start();
            });
        } else {
            this.element.find('#notebook_tour').addClass("disabled");
        }
        this.element.find('#keyboard_shortcuts').click(function () {
            that.quick_help.show_keyboard_shortcuts();
        });
        
        this.update_restore_checkpoint(null);
        
        this.events.on('checkpoints_listed.Notebook', function (event, data) {
            that.update_restore_checkpoint(that.notebook.checkpoints);
        });
        
        this.events.on('checkpoint_created.Notebook', function (event, data) {
            that.update_restore_checkpoint(that.notebook.checkpoints);
        });
        
        this.events.on('notebook_loaded.Notebook', function() {
            var langinfo = that.notebook.metadata.language_info || {};
            that.update_nbconvert_script(langinfo);
        });
        
        this.events.on('kernel_ready.Kernel', function(event, data) {
            var langinfo = data.kernel.info_reply.language_info || {};
            that.update_nbconvert_script(langinfo);
            that.add_kernel_help_links(data.kernel.info_reply.help_links || []);
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
        
        var that = this;
        checkpoints.map(function (checkpoint) {
            var d = new Date(checkpoint.last_modified);
            ul.append(
                $("<li/>").append(
                    $("<a/>")
                    .attr("href", "#")
                    .text(moment(d).format("LLLL"))
                    .click(function () {
                        that.notebook.restore_checkpoint_dialog(checkpoint);
                    })
                )
            );
        });
    };
    
    MenuBar.prototype.update_nbconvert_script = function(langinfo) {
        /**
         * Set the 'Download as foo' menu option for the relevant language.
         */
        var el = this.element.find('#download_script');
        
        // Set menu entry text to e.g. "Python (.py)"
        var langname = (langinfo.name || 'Script');
        langname = langname.charAt(0).toUpperCase()+langname.substr(1); // Capitalise
        el.find('a').text(langname + ' ('+(langinfo.file_extension || 'txt')+')');
    };

    MenuBar.prototype.add_kernel_help_links = function(help_links) {
        /** add links from kernel_info to the help menu */
        var divider = $("#kernel-help-links");
        if (divider.length === 0) {
            // insert kernel help section above about link
            var about = $("#notebook_about").parent();
            divider = $("<li>")
                .attr('id', "kernel-help-links")
                .addClass('divider');
            about.prev().before(divider);
        }
        // remove previous entries
        while (!divider.next().hasClass('divider')) {
            divider.next().remove();
        }
        if (help_links.length === 0) {
            // no help links, remove the divider
            divider.remove();
            return;
        }
        var cursor = divider;
        help_links.map(function (link) {
            cursor.after($("<li>")
                .append($("<a>")
                    .attr('target', '_blank')
                    .attr('title', 'Opens in a new window')
                    .attr('href', link.url)
                    .append($("<i>")
                        .addClass("fa fa-external-link menu-icon pull-right")
                    )
                    .append($("<span>")
                        .text(link.text)
                    )
                )
            );
            cursor = cursor.next();
        });
        
    };

    // Backwards compatability.
    IPython.MenuBar = MenuBar;

    return {'MenuBar': MenuBar};
});
