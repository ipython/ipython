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
        this.element.find('span#save_widget').addClass('ui-widget');
        this.element.find('span#notebook_name').addClass('ui-widget');
        this.element.find('span#save_status').addClass('ui-widget')
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
        $([IPython.events]).on('notebook_loaded.Notebook', function () {
            that.set_last_saved();
            that.update_notebook_name();
            that.update_document_title();
        });
        $([IPython.events]).on('notebook_saved.Notebook', function () {
            that.set_last_saved();
            that.update_notebook_name();
            that.update_document_title();
        });
        $([IPython.events]).on('notebook_save_failed.Notebook', function () {
            that.set_save_status('Last Save Failed!');
        });
    };


    SaveWidget.prototype.rename_notebook = function () {
        var that = this;
        IPython.utils.notebook_name_dialog(
            "Rename Notebook",
            "Enter a new notebook name:",
            function (new_name) {
                IPython.notebook.set_notebook_name(new_name);
                IPython.notebook.save_notebook();
            }
        );
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
        this.element.find('span#save_status').html(msg);
    }


    SaveWidget.prototype.set_last_saved = function () {
        var d = new Date();
        this.set_save_status('Last saved: '+d.format('mmm dd HH:MM'));
    };


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

