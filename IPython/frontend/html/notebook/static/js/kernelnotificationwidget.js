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

    IPython.kernelnotificationwidget = new IPython.NotificationWidget('#notification');

    var knw = IPython.kernelnotificationwidget;
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
        knw.set_message("Restarting kernel");
    });

    $([IPython.events]).on('status_interrupting.Kernel',function () {
        knw.set_message("Interrupting kernel");
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

    var div = $('<div/>').attr('id','notebook_notification');
    $('#notification_area').append(div);
    IPython.notebooknotificationwidget = new IPython.NotificationWidget('#notebook_notification');
    var nnw = IPython.notebooknotificationwidget;


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

    return IPython;

}(IPython));

