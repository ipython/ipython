
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
            var div = $('<div/>').addClass('notebook_item ui-widget ui-widget-content ui-helper-clearfix');
            var nbname = $('<span/>').addClass('item_name').append(
                $('<a/>').attr('href','/'+data[i].notebook_id).
                attr('target','_blank').
                text(data[i].name)
            );
            var buttons = $('<span/>').addClass('item_buttons').append(
                $('<button>Delete</button>').button()
            )
            div.append(nbname).append(buttons);
            this.element.append(div);
        }
    };


    IPython.NotebookList = NotebookList;

    return IPython;

}(IPython));

