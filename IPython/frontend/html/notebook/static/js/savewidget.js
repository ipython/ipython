
//============================================================================
// Cell
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
        this.element.find('input#notebook_name').addClass('ui-widget ui-widget-content');
        this.element.find('button#save_notebook').button();
        var left_panel_width = $('div#left_panel').outerWidth();
        var left_panel_splitter_width = $('div#left_panel_splitter').outerWidth();
        $('span#save_widget').css({marginLeft:left_panel_width+left_panel_splitter_width});
    };


    SaveWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('button#save_notebook').click(function () {
            IPython.notebook.save_notebook(that.get_notebook_name());
        });
    };


    SaveWidget.prototype.get_notebook_name = function () {
        return this.element.find('input#notebook_name').attr('value');
    }


    SaveWidget.prototype.set_notebook_name = function (name) {
        this.element.find('input#notebook_name').attr('value',name);
    }


    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

