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
        this.notebook_name_blacklist_re = /[\/\\]/;
        this.last_saved_name = '';
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };


    SaveWidget.prototype.style = function () {
        this.element.find('span#save_widget').addClass('ui-widget');
        this.element.find('span#notebook_name').addClass('ui-widget ui-widget-content');
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
    };


    SaveWidget.prototype.save_notebook = function () {
        IPython.notebook.save_notebook();
    };


    SaveWidget.prototype.rename_notebook = function () {
        var that = this;
        var dialog = $('<div/>');
        dialog.append(
            $('<h3/>').html('Enter a new notebook name:')
            .css({'margin-bottom': '10px'})
        );
        dialog.append(
            $('<input/>').attr('type','text').attr('size','35')
            .addClass('ui-widget ui-widget-content')
            .attr('value',that.get_notebook_name())
        );
        $(document).append(dialog);
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Rename Notebook",
            closeText: "",
            buttons : {
                "OK": function () {
                    var new_name = $(this).find('input').attr('value');
                    if (!that.test_notebook_name(new_name)) {
                        $(this).find('h3').html(
                            "Invalid notebook name. " +
                            "Notebook names can contain any characters " +
                            "except / and \\. Please enter a new notebook name:"
                        );
                    } else {
                        that.set_notebook_name(new_name);
                        that.save_notebook();
                        $(this).dialog('close');
                    }
                },
                "Cancel": function () {
                    $(this).dialog('close');
                }
            }
        });
    }

    SaveWidget.prototype.notebook_saved = function () {
        this.set_document_title();
        this.last_saved_name = this.get_notebook_name();
    };


    SaveWidget.prototype.get_notebook_name = function () {
        return this.element.find('span#notebook_name').html();
    };


    SaveWidget.prototype.set_notebook_name = function (nbname) {
        this.element.find('span#notebook_name').html(nbname);
        this.set_document_title();
        this.last_saved_name = nbname;
    };


    SaveWidget.prototype.set_document_title = function () {
        nbname = this.get_notebook_name();
        document.title = nbname;
    };
        

    SaveWidget.prototype.get_notebook_id = function () {
        return $('body').data('notebookId');
    };


    SaveWidget.prototype.update_url = function () {
        var notebook_id = this.get_notebook_id();
        if (notebook_id !== '') {
            var new_url = '/'+notebook_id;
            window.history.replaceState({}, '', new_url);
        };
    };


    SaveWidget.prototype.test_notebook_name = function (nbname) {
        if (this.notebook_name_blacklist_re.test(nbname) == false) {
            return true;
        } else {
            return false;
        };
    };


    SaveWidget.prototype.reset_status = function () {
        this.is_renaming();
    };


    SaveWidget.prototype.status_save = function () {
    };


    SaveWidget.prototype.status_saving = function () {
    };


    SaveWidget.prototype.status_loading = function () {
    };


    SaveWidget.prototype.status_rename = function () {
    };


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

