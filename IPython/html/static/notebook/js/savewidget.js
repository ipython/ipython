//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// SaveWidget
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var SaveWidget = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    SaveWidget.prototype.style = function () {
    };


    SaveWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('span#notebook_name').click(function () {
            that.rename_notebook();
        });
        this.element.find('span#notebook_name').hover(function () {
            $(this).addClass("ui-state-hover");
        }, function () {
            $(this).removeClass("ui-state-hover");
        });
        $([IPython.events]).on('notebook_loaded.Notebook', function () {
            that.update_notebook_name();
            that.update_document_title();
        });
        $([IPython.events]).on('notebook_saved.Notebook', function () {
            that.update_notebook_name();
            that.update_document_title();
        });
        $([IPython.events]).on('notebook_save_failed.Notebook', function () {
            that.set_save_status('Autosave Failed!');
        });
        $([IPython.events]).on('checkpoints_listed.Notebook', function (event, data) {
            that.set_last_checkpoint(data[0]);
        });
        
        $([IPython.events]).on('checkpoint_created.Notebook', function (event, data) {
            that.set_last_checkpoint(data);
        });
        $([IPython.events]).on('set_dirty.Notebook', function (event, data) {
            that.set_autosaved(data.value);
        });
    };


    SaveWidget.prototype.rename_notebook = function () {
        var that = this;
        var dialog = $('<div/>').append(
            $("<p/>").addClass("rename-message")
                .html('Enter a new notebook name:')
        ).append(
            $("<br/>")
        ).append(
            $('<input/>').attr('type','text').attr('size','25')
            .val(IPython.notebook.get_notebook_name())
        );
        IPython.dialog.modal({
            title: "Rename Notebook",
            body: dialog,
            buttons : {
                "Cancel": {},
                "OK": {
                    class: "btn-primary",
                    click: function () {
                    var new_name = $(this).find('input').val();
                    if (!IPython.notebook.test_notebook_name(new_name)) {
                        $(this).find('.rename-message').html(
                            "Invalid notebook name. Notebook names must "+
                            "have 1 or more characters and can contain any characters " +
                            "except :/\\. Please enter a new notebook name:"
                        );
                        return false;
                    } else {
                        IPython.notebook.set_notebook_name(new_name);
                        IPython.notebook.save_notebook();
                    }
                }}
                },
            open : function (event, ui) {
                var that = $(this);
                // Upon ENTER, click the OK button.
                that.find('input[type="text"]').keydown(function (event, ui) {
                    if (event.which === utils.keycodes.ENTER) {
                        that.find('.btn-primary').first().click();
                        return false;
                    }
                });
                that.find('input[type="text"]').focus();
            }
        });
    }


    SaveWidget.prototype.update_notebook_name = function () {
        var nbname = IPython.notebook.get_notebook_name();
        this.element.find('span#notebook_name').html(nbname);
    };


    SaveWidget.prototype.update_document_title = function () {
        var nbname = IPython.notebook.get_notebook_name();
        document.title = nbname;
    };


    SaveWidget.prototype.set_save_status = function (msg) {
        this.element.find('span#autosave_status').html(msg);
    }

    SaveWidget.prototype.set_checkpoint_status = function (msg) {
        this.element.find('span#checkpoint_status').html(msg);
    }

    SaveWidget.prototype.set_last_checkpoint = function (checkpoint) {
        if (!checkpoint) {
            this.set_checkpoint_status("");
            return;
        }
        var d = new Date(checkpoint.last_modified);
        this.set_checkpoint_status(
            "Last Checkpoint: " + d.format('mmm dd HH:MM')
        );
    }

    SaveWidget.prototype.set_autosaved = function (dirty) {
        if (dirty) {
            this.set_save_status("(unsaved changes)");
        } else {
            this.set_save_status("(autosaved)");
        }
    };


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

