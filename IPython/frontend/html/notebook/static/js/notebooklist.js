
//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var NotebookList = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    NotebookList.prototype.style = function () {
        this.element.addClass('ui-widget ui-widget-content');
        $('div#project_name').addClass('ui-widget ui-widget-header');
    };


    NotebookList.prototype.bind_events = function () {

    };


    NotebookList.prototype.load_list = function () {
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.list_loaded,this)
        };
        $.ajax("/notebooks", settings);
    };


    NotebookList.prototype.list_loaded = function (data, status, xhr) {
        var len = data.length;
        for (var i=0; i<len; i++) {
            var notebook_id = data[i].notebook_id;
            var nbname = data[i].name;

            var item = $('<div/>');
            item.addClass('notebook_item ui-widget ui-widget-content ui-helper-clearfix');
            var item_name = $('<span/>').addClass('item_name').append(
                $('<a/>').attr('href','/'+notebook_id).
                attr('target','_blank').
                text(nbname)
            );
            // Store the nbname and notebook_id on the item for later usage. We have to do this
            // because the loop over elements changes the values of the local nbname and notebook_id
            // variables.
            item.data('notebook_id',notebook_id);
            item.data('nbname',nbname);

            var buttons = $('<span/>').addClass('item_buttons');
            var delete_button = $('<button>Delete</button>').button().
                click(function (e) {
                    // $(this) is the button that was clicked.
                    var that = $(this);
                    // We use the nbname and notebook_id from the parent notebook_item element's
                    // data because the outer scopes values change as we iterate through the loop.
                    var parent_item = that.parents('div.notebook_item');
                    var nbname = parent_item.data('nbname');
                    var notebook_id = parent_item.data('notebook_id');
                    var dialog = $('<div/>');
                    dialog.html('Are you sure you want to permanently delete the notebook: ' + nbname + '?');
                    parent_item.append(dialog);
                    dialog.dialog({
                        resizable: false,
                        modal: true,
                        title: "Delete notebook",
                        buttons : {
                            "Delete": function () {
                                var settings = {
                                    processData : false,
                                    cache : false,
                                    type : "DELETE",
                                    dataType : "json",
                                    success : function (data, status, xhr) {
                                        parent_item.remove();
                                    }
                                };
                                $.ajax("/notebooks/" + notebook_id, settings);
                                $(this).dialog('close');
                            },
                            "Cancel": function () {
                                $(this).dialog('close');
                            }
                        }
                    });
                });
            buttons.append(delete_button);
            item.append(item_name).append(buttons);
            this.element.append(item);
        }
    };


    IPython.NotebookList = NotebookList;

    return IPython;

}(IPython));

