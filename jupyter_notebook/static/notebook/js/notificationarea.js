define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
    'base/js/notificationarea',
    'moment'
], function(IPython, $, utils, dialog, notificationarea, moment) {
    "use strict";
    var NotificationArea = notificationarea.NotificationArea;
    
    var NotebookNotificationArea = function(selector, options) {
        NotificationArea.apply(this, [selector, options]);
        this.save_widget = options.save_widget;
        this.notebook = options.notebook;
        this.keyboard_manager = options.keyboard_manager;
    };
    
    NotebookNotificationArea.prototype = Object.create(NotificationArea.prototype);
    
    /**
     * Initialize the default set of notification widgets.
     *
     * @method init_notification_widgets
     */
    NotebookNotificationArea.prototype.init_notification_widgets = function () {
        this.init_kernel_notification_widget();
        this.init_notebook_notification_widget();
    };

    /**
     * Initialize the notification widget for kernel status messages.
     *
     * @method init_kernel_notification_widget
     */
    NotebookNotificationArea.prototype.init_kernel_notification_widget = function () {
        var that = this;
        var knw = this.new_notification_widget('kernel');
        var $kernel_ind_icon = $("#kernel_indicator_icon");
        var $modal_ind_icon = $("#modal_indicator");
        var $readonly_ind_icon = $('#readonly-indicator');
        var $body = $('body');

        // Listen for the notebook loaded event.  Set readonly indicator.
        this.events.on('notebook_loaded.Notebook', function() {
            if (that.notebook.writable) {
                $readonly_ind_icon.hide();
            } else {
                $readonly_ind_icon.show();
            }
        });

        // Command/Edit mode
        this.events.on('edit_mode.Notebook', function () {
            that.save_widget.update_document_title();
            $body.addClass('edit_mode');
            $body.removeClass('command_mode');
            $modal_ind_icon.attr('title','Edit Mode');
        });

        this.events.on('command_mode.Notebook', function () {
            that.save_widget.update_document_title();
            $body.removeClass('edit_mode');
            $body.addClass('command_mode');
            $modal_ind_icon.attr('title','Command Mode');
        });

        // Implicitly start off in Command mode, switching to Edit mode will trigger event
        $modal_ind_icon.addClass('modal_indicator').attr('title','Command Mode');
        $body.addClass('command_mode');

        // Kernel events

        // this can be either kernel_created.Kernel or kernel_created.Session
        this.events.on('kernel_created.Kernel kernel_created.Session', function () {
            knw.info("Kernel Created", 500);
        });

        this.events.on('kernel_reconnecting.Kernel', function () {
            knw.warning("Connecting to kernel");
        });

        this.events.on('kernel_connection_dead.Kernel', function (evt, info) {
            knw.danger("Not Connected", undefined, function () {
                // schedule reconnect a short time in the future, don't reconnect immediately
                setTimeout($.proxy(info.kernel.reconnect, info.kernel), 500);
            }, {title: 'click to reconnect'});
        });

        this.events.on('kernel_connected.Kernel', function () {
            knw.info("Connected", 500);
        });

        this.events.on('kernel_restarting.Kernel', function () {
            that.save_widget.update_document_title();
            knw.set_message("Restarting kernel", 2000);
        });

        this.events.on('kernel_autorestarting.Kernel', function (evt, info) {
            // Only show the dialog on the first restart attempt. This
            // number gets tracked by the `Kernel` object and passed
            // along here, because we don't want to show the user 5
            // dialogs saying the same thing (which is the number of
            // times it tries restarting).
            if (info.attempt === 1) {

                dialog.kernel_modal({
                    notebook: that.notebook,
                    keyboard_manager: that.keyboard_manager,
                    title: "Kernel Restarting",
                    body: "The kernel appears to have died. It will restart automatically.",
                    buttons: {
                        OK : {
                            class : "btn-primary"
                        }
                    }
                });
            }

            that.save_widget.update_document_title();
            knw.danger("Dead kernel");
            $kernel_ind_icon.attr('class','kernel_dead_icon').attr('title','Kernel Dead');
        });

        this.events.on('kernel_interrupting.Kernel', function () {
            knw.set_message("Interrupting kernel", 2000);
        });

        this.events.on('kernel_disconnected.Kernel', function () {
            $kernel_ind_icon
                .attr('class', 'kernel_disconnected_icon')
                .attr('title', 'No Connection to Kernel');
        });

        this.events.on('kernel_connection_failed.Kernel', function (evt, info) {
            // only show the dialog if this is the first failed
            // connect attempt, because the kernel will continue
            // trying to reconnect and we don't want to spam the user
            // with messages
            if (info.attempt === 1) {

                var msg = "A connection to the notebook server could not be established." +
                        " The notebook will continue trying to reconnect, but" +
                        " until it does, you will NOT be able to run code. Check your" +
                        " network connection or notebook server configuration.";

                dialog.kernel_modal({
                    title: "Connection failed",
                    body: msg,
                    keyboard_manager: that.keyboard_manager,
                    notebook: that.notebook,
                    buttons : {
                        "OK": {}
                    }
                });
            }
        });

        this.events.on('kernel_killed.Kernel kernel_killed.Session', function () {
            that.save_widget.update_document_title();
            knw.warning("No kernel");
            $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel is not running');
        });

        this.events.on('kernel_dead.Kernel', function () {

            var showMsg = function () {

                var msg = 'The kernel has died, and the automatic restart has failed.' +
                        ' It is possible the kernel cannot be restarted.' +
                        ' If you are not able to restart the kernel, you will still be able to save' +
                        ' the notebook, but running code will no longer work until the notebook' +
                        ' is reopened.';

                dialog.kernel_modal({
                    title: "Dead kernel",
                    body : msg,
                    keyboard_manager: that.keyboard_manager,
                    notebook: that.notebook,
                    buttons : {
                        "Manual Restart": {
                            class: "btn-danger",
                            click: function () {
                                that.notebook.start_session();
                            }
                        },
                    "Don't restart": {}
                    }
                });

                return false;
            };

            that.save_widget.update_document_title();
            knw.danger("Dead kernel", undefined, showMsg);
            $kernel_ind_icon.attr('class','kernel_dead_icon').attr('title','Kernel Dead');

            showMsg();
        });
        
        this.events.on("no_kernel.Kernel", function (evt, data) {
            $("#kernel_indicator").find('.kernel_indicator_name').text("No Kernel");
        });

        this.events.on('kernel_dead.Session', function (evt, info) {
            var full = info.xhr.responseJSON.message;
            var short = info.xhr.responseJSON.short_message || 'Kernel error';
            var traceback = info.xhr.responseJSON.traceback;

            var showMsg = function () {
                var msg = $('<div/>').append($('<p/>').text(full));
                var cm, cm_elem, cm_open;

                if (traceback) {
                    cm_elem = $('<div/>')
                        .css('margin-top', '1em')
                        .css('padding', '1em')
                        .addClass('output_scroll');
                    msg.append(cm_elem);
                    cm = CodeMirror(cm_elem.get(0), {
                        mode:  "python",
                        readOnly : true
                    });
                    cm.setValue(traceback);
                    cm_open = $.proxy(cm.refresh, cm);
                }

                dialog.kernel_modal({
                    title: "Failed to start the kernel",
                    body : msg,
                    keyboard_manager: that.keyboard_manager,
                    notebook: that.notebook,
                    open: cm_open,
                    buttons : {
                        "Ok": { class: 'btn-primary' }
                    }
                });

                return false;
            };

            that.save_widget.update_document_title();
            $kernel_ind_icon.attr('class','kernel_dead_icon').attr('title','Kernel Dead');
            knw.danger(short, undefined, showMsg);
        });

        this.events.on('kernel_starting.Kernel kernel_created.Session', function () {
            window.document.title='(Starting) '+window.document.title;
            $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel Busy');
            knw.set_message("Kernel starting, please wait...");
        });

        this.events.on('kernel_ready.Kernel', function () {
            that.save_widget.update_document_title();
            $kernel_ind_icon.attr('class','kernel_idle_icon').attr('title','Kernel Idle');
            knw.info("Kernel ready", 500);
        });

        this.events.on('kernel_idle.Kernel', function () {
            that.save_widget.update_document_title();
            $kernel_ind_icon.attr('class','kernel_idle_icon').attr('title','Kernel Idle');
        });

        this.events.on('kernel_busy.Kernel', function () {
            window.document.title='(Busy) '+window.document.title;
            $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel Busy');
        });

        this.events.on('spec_match_found.Kernel', function (evt, data) {
            that.widget('kernelspec').info("Using kernel: " + data.found.spec.display_name, 3000, undefined, {
                title: "Only candidate for language: " + data.selected.language + " was " + data.found.spec.display_name
            });
        });

        
        // Start the kernel indicator in the busy state, and send a kernel_info request.
        // When the kernel_info reply arrives, the kernel is idle.
        $kernel_ind_icon.attr('class','kernel_busy_icon').attr('title','Kernel Busy');
    };

    /**
     * Initialize the notification widget for notebook status messages.
     *
     * @method init_notebook_notification_widget
     */
    NotebookNotificationArea.prototype.init_notebook_notification_widget = function () {
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
        this.events.on('notebook_save_failed.Notebook', function (evt, error) {
            nnw.warning(error.message || "Notebook save failed");
        });
        this.events.on('notebook_copy_failed.Notebook', function (evt, error) {
            nnw.warning(error.message || "Notebook copy failed");
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

    // Backwards compatibility.
    IPython.NotificationArea = NotebookNotificationArea;
    
    return {'NotebookNotificationArea': NotebookNotificationArea};
});
