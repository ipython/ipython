// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
    'base/js/keyboard',
    'dateformat',
], function(IPython, $, utils, dialog, keyboard) {
    "use strict";

    var SaveWidget = function (selector, options) {
        // TODO: Remove circulat ref.
        this.notebook = undefined;
        this.selector = selector;
        this.events = options.events;
        this.keyboard_manager = options.keyboard_manager;
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
        this.events.on('notebook_loaded.Notebook', function () {
            that.update_notebook_name();
            that.update_document_title();
        });
        this.events.on('notebook_saved.Notebook', function () {
            that.update_notebook_name();
            that.update_document_title();
        });
        this.events.on('notebook_renamed.Notebook', function () {
            that.update_notebook_name();
            that.update_document_title();
            that.update_address_bar();
        });
        this.events.on('notebook_save_failed.Notebook', function () {
            that.set_save_status('Autosave Failed!');
        });
        this.events.on('checkpoints_listed.Notebook', function (event, data) {
            that.set_last_checkpoint(data[0]);
        });

        this.events.on('checkpoint_created.Notebook', function (event, data) {
            that.set_last_checkpoint(data);
        });
        this.events.on('set_dirty.Notebook', function (event, data) {
            that.set_autosaved(data.value);
        });
    };


    SaveWidget.prototype.rename_notebook = function (options) {
        options = options || {};
        var that = this;
        var dialog_body = $('<div/>').append(
            $("<p/>").addClass("rename-message")
                .text('Enter a new notebook name:')
        ).append(
            $("<br/>")
        ).append(
            $('<input/>').attr('type','text').attr('size','25').addClass('form-control')
            .val(that.notebook.get_notebook_name())
        );
        dialog.modal({
            title: "Rename Notebook",
            body: dialog_body,
            notebook: options.notebook,
            keyboard_manager: this.keyboard_manager,
            buttons : {
                "Cancel": {},
                "OK": {
                    class: "btn-primary",
                    click: function () {
                    var new_name = $(this).find('input').val();
                    if (!that.notebook.test_notebook_name(new_name)) {
                        $(this).find('.rename-message').text(
                            "Invalid notebook name. Notebook names must "+
                            "have 1 or more characters and can contain any characters " +
                            "except :/\\. Please enter a new notebook name:"
                        );
                        return false;
                    } else {
                        that.notebook.rename(new_name);
                    }
                }}
                },
            open : function (event, ui) {
                var that = $(this);
                // Upon ENTER, click the OK button.
                that.find('input[type="text"]').keydown(function (event, ui) {
                    if (event.which === keyboard.keycodes.enter) {
                        that.find('.btn-primary').first().click();
                        return false;
                    }
                });
                that.find('input[type="text"]').focus().select();
            }
        });
    };


    SaveWidget.prototype.update_notebook_name = function () {
        var nbname = this.notebook.get_notebook_name();
        this.element.find('span#notebook_name').text(nbname);
    };


    SaveWidget.prototype.update_document_title = function () {
        var nbname = this.notebook.get_notebook_name();
        document.title = nbname;
    };
    
    SaveWidget.prototype.update_address_bar = function(){
        var base_url = this.notebook.base_url;
        var nbname = this.notebook.notebook_name;
        var path = this.notebook.notebook_path;
        var state = {path : path, name: nbname};
        window.history.replaceState(state, "", utils.url_join_encode(
            base_url,
            "notebooks",
            path,
            nbname)
        );
    };


    SaveWidget.prototype.set_save_status = function (msg) {
        this.element.find('span#autosave_status').text(msg);
    };

    SaveWidget.prototype.set_checkpoint_status = function (msg) {
        this.element.find('span#checkpoint_status').text(msg);
    };

    SaveWidget.prototype.set_last_checkpoint = function (checkpoint) {
        if (!checkpoint) {
            this.set_checkpoint_status("");
            return;
        }
        var d = new Date(checkpoint.last_modified);
        this.set_checkpoint_status(
            "Last Checkpoint: " + d.format('mmm dd HH:MM')
        );
    };

    SaveWidget.prototype.set_autosaved = function (dirty) {
        if (dirty) {
            this.set_save_status("(unsaved changes)");
        } else {
            this.set_save_status("(autosaved)");
        }
    };

    // Backwards compatability.
    IPython.SaveWidget = SaveWidget;

    return {'SaveWidget': SaveWidget};

});
