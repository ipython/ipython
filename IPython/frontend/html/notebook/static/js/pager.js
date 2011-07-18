
//============================================================================
// Pager
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Pager = function (pager_selector, pager_toggle_selector) {
        this.pager_element = $(pager_selector);
        this.pager_toggle_element = $(pager_toggle_selector);
        this.style();
        this.bind_events();
        this.collapse();
    };


    Pager.prototype.style = function () {
        this.pager_toggle_element.addClass('ui-widget ui-widget-content')
        this.pager_element.addClass('')
    };


    Pager.prototype.bind_events = function () {
        var that = this;
        this.pager_toggle_element.click(function () {
            that.pager_element.toggle('fast');
        });

        this.pager_toggle_element.hover(
            function () {
                that.pager_toggle_element.addClass('ui-state-hover');
            },
            function () {
                that.pager_toggle_element.removeClass('ui-state-hover');
            }
        );
    };


    Pager.prototype.collapse = function () {
        this.pager_element.hide('fast');
    };


    Pager.prototype.expand = function () {
        this.pager_element.show('fast');
    };


    Pager.prototype.clear = function (text) {
        this.pager_element.empty();
    };


    Pager.prototype.append_text = function (text) {
        var toinsert = $("<div/>").addClass("output_area output_stream monospace-font");
        toinsert.append($("<pre/>").addClass("monospace-font").
            html(utils.fixConsole(text)));
        this.pager_element.append(toinsert);
    };   


    IPython.Pager = Pager;

    return IPython;

}(IPython));

