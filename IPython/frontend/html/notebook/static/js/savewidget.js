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
        this.element.find('input#notebook_name').addClass('ui-widget ui-widget-content');
        this.element.find('input#notebook_name').attr('tabindex','1');
        this.element.find('button#save_notebook').button();
        this.element.find('button#save_notebook').attr('title', 'Save the Notebook');
        var left_panel_width = $('div#left_panel').outerWidth();
        var left_panel_splitter_width = $('div#left_panel_splitter').outerWidth();
        $('span#save_widget').css({marginLeft:left_panel_width+left_panel_splitter_width});

    };


    SaveWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('button#save_notebook').click(function () {
            that.save_notebook();
        });
        this.element.find('input#notebook_name').keyup(function () {
            that.is_renaming();
        });
    };


    SaveWidget.prototype.save_notebook = function () {
        IPython.notebook.save_notebook();
    };


    SaveWidget.prototype.notebook_saved = function () {
        this.set_document_title();
        this.last_saved_name = this.get_notebook_name();
    };


    SaveWidget.prototype.is_renaming = function () {
        if (this.get_notebook_name() !== this.last_saved_name) {
            this.status_rename();
        } else {
            this.status_save();
        };
    };


    SaveWidget.prototype.get_notebook_name = function () {
        return this.element.find('input#notebook_name').attr('value');
    };


    SaveWidget.prototype.set_notebook_name = function (nbname) {
        this.element.find('input#notebook_name').attr('value',nbname);
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
            window.history.replaceState({}, '', notebook_id);
        };
    };


    SaveWidget.prototype.test_notebook_name = function () {
        var nbname = this.get_notebook_name();
        if (this.notebook_name_blacklist_re.test(nbname) == false) {
            return true;
        } else {
            var bad_name = $('<div/>');
            bad_name.html(
                "The notebook name you entered (" +
                nbname +
                ") is not valid. Notebook names can contain any characters except / and \\."
            );
            bad_name.dialog({title: 'Invalid name', modal: true});
            return false;
        };
    };


    SaveWidget.prototype.reset_status = function () {
        this.is_renaming();
    };


    SaveWidget.prototype.status_save = function () {
        this.element.find('button#save_notebook').button('option', 'label', '<u>S</u>ave');
        this.element.find('button#save_notebook').button('enable');
        IPython.print_widget.enable();
    };


    SaveWidget.prototype.status_saving = function () {
        this.element.find('button#save_notebook').button('option', 'label', 'Saving');
        this.element.find('button#save_notebook').button('disable');
        IPython.print_widget.disable();
    };


    SaveWidget.prototype.status_loading = function () {
        this.element.find('button#save_notebook').button('option', 'label', 'Loading');
        this.element.find('button#save_notebook').button('disable');
        IPython.print_widget.disable();
    };    


    SaveWidget.prototype.status_rename = function () {
        this.element.find('button#save_notebook').button('option', 'label', 'Rename');
        this.element.find('button#save_notebook').button('enable');
        IPython.print_widget.enable();
    };


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

