//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Tabs
//============================================================================


var IPython = (function (IPython) {

    var TabManager = function (selector) {
        this.tabs = $(selector).tabs();
        this.tabs.find('.ui-tabs-nav').sortable({
            axis: "x",
            update: function () {
                // refresh the code mirror for all the worksheets
                var sheets = IPython.notebook.get_worksheets();
                for (var i=0; i<sheets.length; i++) {
                    sheets[i].refresh_code_mirror();
                }
            }
        });
        this.tabs.addClass('container');
        this.tabs.tabs('add','#tab-add','+') // create a button for adding tabs
        this.bind_events();
    };


    TabManager.prototype.bind_events = function () {
        that = this;
        // attach click event to the 'Add Tab' button
        $('div#tabs').find("a[href='#tab-add']").parent('li').click(function (event) {
            event.preventDefault();
            var nsheets = IPython.notebook.nsheets();
            IPython.notebook.insert_worksheet_above('New Tab ' + (nsheets+1), nsheets);
        })
        // attach event handler for when a tab is added
        this.tabs.bind("tabsadd", function(event, ui) {
            // select the tab and panels
            var tab = $(ui.tab);
            // set click and hover events
            var e = tab.children('span');
            e.click(that.set_onclick);
            e.hover(function () {
                if($(this).closest('li').hasClass('ui-tabs-active') && !$(this).hasClass('editing')) {
                    $(this).addClass("ui-state-hover");
                }
            }, function () {
                if($(this).closest('li').hasClass('ui-tabs-active')) {
                    $(this).removeClass("ui-state-hover");
                }
            });
            // add a close icon to the tab
            tab.after('<span class="ui-icon ui-icon-close"></span>');
            tab.next().click(that.close_tab);
            // set class for tab panel
            $(ui.panel).addClass('panel');
        });
        // attach event handler for when a tab is selected
        this.tabs.bind("tabsshow", function(event, ui) {
            // ignore if the "add tab" button was clicked
            if($(ui.panel).attr('id') !== 'tab-add') {
                var ws = IPython.notebook.get_worksheet(ui.index);
                if(ws !== undefined) {
                    if(ws.ncells() === 0) {
                        ws.insert_cell_below('code');
                    }
                }
                ws.refresh_code_mirror();
                // reselect the cell, since the cell loses focus when the tab is changed
                var i = ws.get_selected_index();
                ws.select(i);
            }
        })
    };

    TabManager.prototype.set_onclick = function () {
        // check whether tab is active by checking whether the containing 'li' contains some active class
        if($(this).closest('li').hasClass('ui-tabs-active')) {
            // create a textbox with title as current value
            var curr_label = $(this).text();
            var editableText = $('<input/>').attr('type','text').attr('size',10);
            editableText.val(curr_label);
            $(this).html(editableText);
            editableText.focus();
            // designate tab as in editing mode
            $(this).removeClass("ui-state-hover");
            $(this).addClass('editing');
            // event handler for when the user clicks outside the textbox (i.e., is done editing)
            editableText.blur( function() {
                var new_label = null;
                if($(this).val()) {
                    new_label = $(this).val();
                } else {
                    new_label = curr_label;
                }
                IPython.notebook.get_selected_worksheet().set_worksheet_name(new_label);
                $(this).parent('span').removeClass('editing');
                $(this).replaceWith(new_label);
            });
        }
    }

    TabManager.prototype.close_tab = function () {
        var index = $(this).closest('ul.ui-tabs-nav').children().index($(this).closest('li'));
        var dialog = $('<div/>');
        dialog.html('Do you want to close this tab?  You will lose all work in this worksheet.');
        dialog.dialog({
            resizable: false,
            modal: true,
            title: "Close Tab",
            closeText: "",
            close: function(event, ui) {$(this).dialog('destroy').remove();},
            buttons: {
                "OK": function () {
                    IPython.notebook.delete_worksheet(index);
                    $(this).dialog('close');
                },
                "Cancel": function () {
                    $(this).dialog('close');
                }
            }
        })
    }


    IPython.TabManager = TabManager;

    return IPython;

}(IPython));

