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
        this.element.find('span#save_status').addClass('ui-widget ui-widget-content')
            .css({border: 'none', 'margin-left': '20px'});
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
            $('<input/>').attr('type','text').attr('size','25')
            .addClass('ui-widget ui-widget-content')
            .attr('value',that.get_notebook_name())
        );
        // $(document).append(dialog);
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Rename Notebook",
            closeText: "",
            close: function(event, ui) {$(this).dialog('destroy').remove();},
            buttons : {
                "OK": function () {
                    var new_name = $(this).find('input').attr('value');
                    if (!that.test_notebook_name(new_name)) {
                        $(this).find('h3').html(
                            "Invalid notebook name. Notebook names must "+
                            "have 1 or more characters and can contain any characters " +
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
        nbname = nbname || '';
        if (this.notebook_name_blacklist_re.test(nbname) == false && nbname.length>0) {
            return true;
        } else {
            return false;
        };
    };


    SaveWidget.prototype.set_last_saved = function () {
        var d = new Date();
        $('#save_status').html('Last saved: '+d.format('mmm dd h:MM TT'));
        
    };

    SaveWidget.prototype.reset_status = function () {
        this.element.find('span#save_status').html('');
    };


    SaveWidget.prototype.status_last_saved = function () {
        this.set_last_saved();
    };


    SaveWidget.prototype.status_saving = function () {
        this.element.find('span#save_status').html('Saving...');
    };


    SaveWidget.prototype.status_save_failed = function () {
        this.element.find('span#save_status').html('Save failed');
    };


    SaveWidget.prototype.status_loading = function () {
        this.element.find('span#save_status').html('Loading...');
    };


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

