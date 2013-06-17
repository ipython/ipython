//----------------------------------------------------------------------------
//  Copyright (C) 2012 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notification widget
//============================================================================

var IPython = (function (IPython) {
    "use strict";
    var utils = IPython.utils;


    var NotificationArea = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
        }
        this.widget_dict = {};
    };

    NotificationArea.prototype.temp_message = function (msg, timeout, css_class) {
        var uuid = utils.uuid();
        if( css_class == 'danger') {css_class = 'ui-state-error';}
        if( css_class == 'warning') {css_class = 'ui-state-highlight';}
        var tdiv = $('<div>')
            .attr('id',uuid)
            .addClass('notification_widget ui-widget ui-widget-content ui-corner-all')
            .addClass('border-box-sizing')
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
        if(this.widget_dict[name] == undefined) {
            return this.new_notification_widget(name);
        }
        return this.get_widget(name);
    };

    NotificationArea.prototype.get_widget = function(name) {
        if(this.widget_dict[name] == undefined) {
            throw('no widgets with this name');
        }
        return this.widget_dict[name];
    };

    NotificationArea.prototype.new_notification_widget = function(name) {
        if(this.widget_dict[name] != undefined) {
            throw('widget with that name already exists ! ');
        }
        var div = $('<div/>').attr('id','notification_'+name);
        $(this.selector).append(div);
        this.widget_dict[name] = new IPython.NotificationWidget('#notification_'+name);
        return this.widget_dict[name];
    };

    NotificationArea.prototype.init_notification_widgets = function() {
        var knw = this.new_notification_widget('kernel');

        // Kernel events
        $([IPython.events]).on('status_idle.Kernel',function () {
            IPython.save_widget.update_document_title();
            knw.set_message('Kernel Idle',200);
            }
        );

        $([IPython.events]).on('status_busy.Kernel',function () {
            window.document.title='(Busy) '+window.document.title;
            knw.set_message("Kernel busy");
        });

        $([IPython.events]).on('status_restarting.Kernel',function () {
            IPython.save_widget.update_document_title();
            knw.set_message("Restarting kernel", 2000);
        });

        $([IPython.events]).on('status_interrupting.Kernel',function () {
            knw.set_message("Interrupting kernel");
        });

        $([IPython.events]).on('status_dead.Kernel',function () {
            var msg = 'The kernel has died, and the automatic restart has failed.' +
                ' It is possible the kernel cannot be restarted.' +
                ' If you are not able to restart the kernel, you will still be able to save' +
                ' the notebook, but running code will no longer work until the notebook' +
                ' is reopened.';

            IPython.dialog.modal({
                title: "Dead kernel",
                body : msg,
                buttons : {
                    "Manual Restart": {
                        class: "btn-danger",
                        click: function () {
                            $([IPython.events]).trigger('status_restarting.Kernel');
                            IPython.notebook.start_kernel();
                        }
                    },
                    "Don't restart": {}
                }
            });
        });

        $([IPython.events]).on('websocket_closed.Kernel', function (event, data) {
            var kernel = data.kernel;
            var ws_url = data.ws_url;
            var early = data.early;
            var msg;
            if (!early) {
                    knw.set_message('Reconnecting WebSockets', 1000);
                    setTimeout(function () {
                        kernel.start_channels();
                    }, 5000);
                return;
            }
            console.log('WebSocket connection failed: ', ws_url)
            msg = "A WebSocket connection to could not be established." +
                " You will NOT be able to run code. Check your" +
                " network connection or notebook server configuration.";
            IPython.dialog.modal({
                title: "WebSocket connection failed",
                body: msg,
                buttons : {
                    "OK": {},
                    "Reconnect": {
                        click: function () {
                            knw.set_message('Reconnecting WebSockets', 1000);
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
        $([IPython.events]).on('notebook_loading.Notebook', function () {
            nnw.set_message("Loading notebook",500);
        });
        $([IPython.events]).on('notebook_loaded.Notebook', function () {
            nnw.set_message("Notebook loaded",500);
        });
        $([IPython.events]).on('notebook_saving.Notebook', function () {
            nnw.set_message("Saving notebook",500);
        });
        $([IPython.events]).on('notebook_saved.Notebook', function () {
            nnw.set_message("Notebook saved",2000);
        });
        $([IPython.events]).on('notebook_save_failed.Notebook', function () {
            nnw.set_message("Notebook save failed");
        });
        
        // Checkpoint events
        $([IPython.events]).on('checkpoint_created.Notebook', function (evt, data) {
            var msg = "Checkpoint created";
            if (data.last_modified) {
                var d = new Date(data.last_modified);
                msg = msg + ": " + d.format("HH:MM:ss");
            }
            nnw.set_message(msg, 2000);
        });
        $([IPython.events]).on('checkpoint_failed.Notebook', function () {
            nnw.set_message("Checkpoint failed");
        });
        $([IPython.events]).on('checkpoint_deleted.Notebook', function () {
            nnw.set_message("Checkpoint deleted", 500);
        });
        $([IPython.events]).on('checkpoint_delete_failed.Notebook', function () {
            nnw.set_message("Checkpoint delete failed");
        });
        $([IPython.events]).on('checkpoint_restoring.Notebook', function () {
            nnw.set_message("Restoring to checkpoint...", 500);
        });
        $([IPython.events]).on('checkpoint_restore_failed.Notebook', function () {
            nnw.set_message("Checkpoint restore failed");
        });

        // Autosave events
        $([IPython.events]).on('autosave_disabled.Notebook', function () {
            nnw.set_message("Autosave disabled", 2000);
        });
        $([IPython.events]).on('autosave_enabled.Notebook', function (evt, interval) {
            nnw.set_message("Saving every " + interval / 1000 + "s", 1000);
        });

    };

    IPython.NotificationArea = NotificationArea;

    return IPython;

}(IPython));

