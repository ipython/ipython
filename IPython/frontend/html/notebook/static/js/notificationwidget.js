//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notification widget
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;


    var NotificationWidget = function (selector) {
        this.selector = selector;
        this.timeout = null;
        this.busy = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    NotificationWidget.prototype.style = function () {
        this.element.addClass('ui-widget ui-widget-content ui-corner-all');
        this.element.addClass('border-box-sizing');
    };


    NotificationWidget.prototype.bind_events = function () {
        var that = this;
        // Kernel events
        $([IPython.events]).on('status_idle.Kernel',function () {
            IPython.save_widget.update_document_title();
            if (that.get_message() === 'Kernel busy') {
                that.element.fadeOut(100, function () {
                    that.element.html('');
                });
            };
        });
        $([IPython.events]).on('status_busy.Kernel',function () {
            window.document.title='(Busy) '+window.document.title;
            that.set_message("Kernel busy");
        });
        $([IPython.events]).on('status_restarting.Kernel',function () {
            IPython.save_widget.update_document_title();
            that.set_message("Restarting kernel",500);
        });
        $([IPython.events]).on('status_interrupting.Kernel',function () {
            that.set_message("Interrupting kernel",500);
        });
        $([IPython.events]).on('status_dead.Kernel',function () {
            var dialog = $('<div/>');
            dialog.html('The kernel has died, would you like to restart it? If you do not restart the kernel, you will be able to save the notebook, but running code will not work until the notebook is reopened.');
            $(document).append(dialog);
            dialog.dialog({
                resizable: false,
                modal: true,
                title: "Dead kernel",
                buttons : {
                    "Restart": function () {
                        $([IPython.events]).trigger('status_restarting.Kernel');
                        IPython.notebook.start_kernel();
                        $(this).dialog('close');
                    },
                    "Continue running": function () {
                        $(this).dialog('close');
                    }
                }
            });
        });
        // Notebook events
        $([IPython.events]).on('notebook_loading.Notebook', function () {
            that.set_message("Loading notebook",500);
        });
        $([IPython.events]).on('notebook_loaded.Notebook', function () {
            that.set_message("Notebook loaded",500);
        });
        $([IPython.events]).on('notebook_saving.Notebook', function () {
            that.set_message("Saving notebook",500);
        });
        $([IPython.events]).on('notebook_saved.Notebook', function () {
            that.set_message("Notebook saved",2000);
        });
        $([IPython.events]).on('notebook_save_failed.Notebook', function () {
            that.set_message("Notebook save failed",2000);
        });
    };


    NotificationWidget.prototype.set_message = function (msg, timeout) {
        var that = this;
        this.element.html(msg);
        this.element.fadeIn(100);
        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        };
        if (timeout !== undefined) {
            this.timeout = setTimeout(function () {
                that.element.fadeOut(100, function () {that.element.html('');});
                that.timeout = null;
            }, timeout)
        };
    };


    NotificationWidget.prototype.get_message = function () {
        return this.element.html();
    };


    IPython.NotificationWidget = NotificationWidget;

    return IPython;

}(IPython));

