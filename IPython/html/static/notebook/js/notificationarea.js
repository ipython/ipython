// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
    'notebook/js/notificationwidget',
    'moment'
], function(IPython, $, utils, dialog, notificationwidget, moment) {
    "use strict";

    var NotificationArea = function (selector, options) {
        // Constructor
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          notebook: Notebook instance
        //          events: $(Events) instance
        //          save_widget: SaveWidget instance
        this.selector = selector;
        this.events = options.events;
        this.save_widget = options.save_widget;
        this.notebook = options.notebook;
        this.keyboard_manager = options.keyboard_manager;
        if (this.selector !== undefined) {
            this.element = $(selector);
        }
        this.widget_dict = {};
    };

    NotificationArea.prototype.temp_message = function (msg, timeout, css_class) {
        var tdiv = $('<div>')
            .addClass('notification_widget')
            .addClass(css_class)
            .hide()
            .text(msg);

        $(this.selector).append(tdiv);
        var tmout = Math.max(1500,(timeout||1500));
        tdiv.fadeIn(100);

        setTimeout(function () {
                tdiv.fadeOut(100, function () {tdiv.remove();});
            }, tmout);
    };

    NotificationArea.prototype.widget = function(name) {
        if(this.widget_dict[name] === undefined) {
            return this.new_notification_widget(name);
        }
        return this.get_widget(name);
    };

    NotificationArea.prototype.get_widget = function(name) {
        if(this.widget_dict[name] === undefined) {
            throw('no widgets with this name');
        }
        return this.widget_dict[name];
    };

    NotificationArea.prototype.new_notification_widget = function(name) {
        if(this.widget_dict[name] !== undefined) {
            throw('widget with that name already exists ! ');
        }
        var div = $('<div/>').attr('id','notification_'+name);
        $(this.selector).append(div);
        this.widget_dict[name] = new notificationwidget.NotificationWidget('#notification_'+name);
        return this.widget_dict[name];
    };

    NotificationArea.prototype.init_notification_widgets = function() {
        var that = this;
        var knw = this.new_notification_widget('kernel');
        var $kernel_ind_icon = $("#kernel_indicator_icon");
        var $modal_ind_icon = $("#modal_indicator_icon");

        // Command/Edit mode
        this.events.on('edit_mode.Notebook',function () {
            that.save_widget.update_document_title();
            $modal_ind_icon.attr('class','edit_mode_icon').attr('title','Edit Mode');
        });

        this.events.on('command_mode.Notebook',function () {
            that.save_widget.update_document_title();
            $modal_ind_icon.attr('class','command_mode_icon').attr('title','Command Mode');
        });

        // Implicitly start off in Command mode, switching to Edit mode will trigger event
        $modal_ind_icon.attr('class','command_mode_icon').attr('title','Command Mode');

        // Kernel events
        this.events.on('status_idle.Kernel',function () {
            that.save_widget.update_document_title();
            $kernel_ind_icon.attr('class','kernel_idle_icon').attr('title','Kernel Idle');
        });

        this.events.on('status_busy.Kernel',function () {
            window.document.title='(Busy) '+window.document.title;
            $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel Busy');
        });

        this.events.on('status_restarting.Kernel',function () {
            that.save_widget.update_document_title();
            knw.set_message("Restarting kernel", 2000);
        });

        this.events.on('status_dead.Kernel',function () {
            that.save_widget.update_document_title();
            knw.danger("Dead kernel");
            $kernel_ind_icon.attr('class','kernel_dead_icon').attr('title','Kernel Dead');
        });

        this.events.on('status_interrupting.Kernel',function () {
            knw.set_message("Interrupting kernel", 2000);
        });
        
        // Start the kernel indicator in the busy state, and send a kernel_info request.
        // When the kernel_info reply arrives, the kernel is idle.
        $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel Busy');

        this.events.on('status_started.Kernel', function (evt, data) {
            knw.info("Websockets Connected", 500);
            that.events.trigger('status_busy.Kernel');
            data.kernel.kernel_info(function () {
                that.events.trigger('status_idle.Kernel');
            });
        });

        this.events.on('status_dead.Kernel',function () {
            var msg = 'The kernel has died, and the automatic restart has failed.' +
                ' It is possible the kernel cannot be restarted.' +
                ' If you are not able to restart the kernel, you will still be able to save' +
                ' the notebook, but running code will no longer work until the notebook' +
                ' is reopened.';

            dialog.modal({
                title: "Dead kernel",
                body : msg,
                keyboard_manager: that.keyboard_manager,
                notebook: that.notebook,
                buttons : {
                    "Manual Restart": {
                        class: "btn-danger",
                        click: function () {
                            that.events.trigger('status_restarting.Kernel');
                            that.notebook.start_kernel();
                        }
                    },
                    "Don't restart": {}
                }
            });
        });

        this.events.on('websocket_closed.Kernel', function (event, data) {
            var kernel = data.kernel;
            var ws_url = data.ws_url;
            var early = data.early;
            var msg;

            $kernel_ind_icon
                .attr('class', 'kernel_disconnected_icon')
                .attr('title', 'No Connection to Kernel');
            
            if (!early) {
                    knw.warning('Reconnecting');
                    setTimeout(function () {
                        kernel.start_channels();
                    }, 5000);
                return;
            }
            console.log('WebSocket connection failed: ', ws_url);
            msg = "A WebSocket connection could not be established." +
                " You will NOT be able to run code. Check your" +
                " network connection or notebook server configuration.";
            dialog.modal({
                title: "WebSocket connection failed",
                body: msg,
                keyboard_manager: that.keyboard_manager,
                notebook: that.notebook,
                buttons : {
                    "OK": {},
                    "Reconnect": {
                        click: function () {
                            knw.warning('Reconnecting');
                            setTimeout(function () {
                                kernel.start_channels();
                            }, 5000);
                        }
                    }
                }
            });
        });


        var nnw = this.new_notification_widget('notebook');

        // Notebook events
        this.events.on('notebook_loading.Notebook', function () {
            nnw.set_message("Loading notebook",500);
        });
        this.events.on('notebook_loaded.Notebook', function () {
            nnw.set_message("Notebook loaded",500);
        });
        this.events.on('notebook_saving.Notebook', function () {
            nnw.set_message("Saving notebook",500);
        });
        this.events.on('notebook_saved.Notebook', function () {
            nnw.set_message("Notebook saved",2000);
        });
        this.events.on('notebook_save_failed.Notebook', function (evt, xhr, status, data) {
            nnw.warning(data || "Notebook save failed");
        });
        
        // Checkpoint events
        this.events.on('checkpoint_created.Notebook', function (evt, data) {
            var msg = "Checkpoint created";
            if (data.last_modified) {
                var d = new Date(data.last_modified);
                msg = msg + ": " + moment(d).format("HH:mm:ss");
            }
            nnw.set_message(msg, 2000);
        });
        this.events.on('checkpoint_failed.Notebook', function () {
            nnw.warning("Checkpoint failed");
        });
        this.events.on('checkpoint_deleted.Notebook', function () {
            nnw.set_message("Checkpoint deleted", 500);
        });
        this.events.on('checkpoint_delete_failed.Notebook', function () {
            nnw.warning("Checkpoint delete failed");
        });
        this.events.on('checkpoint_restoring.Notebook', function () {
            nnw.set_message("Restoring to checkpoint...", 500);
        });
        this.events.on('checkpoint_restore_failed.Notebook', function () {
            nnw.warning("Checkpoint restore failed");
        });

        // Autosave events
        this.events.on('autosave_disabled.Notebook', function () {
            nnw.set_message("Autosave disabled", 2000);
        });
        this.events.on('autosave_enabled.Notebook', function (evt, interval) {
            nnw.set_message("Saving every " + interval / 1000 + "s", 1000);
        });

    };

    IPython.NotificationArea = NotificationArea;

    return {'NotificationArea': NotificationArea};
});
