
//============================================================================
// Pager
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Pager = function (pager_selector, pager_splitter_selector) {
        this.pager_element = $(pager_selector);
        this.pager_splitter_element = $(pager_splitter_selector);
        this.expanded = true;
        this.percentage_height = 0.30;
        this.style();
        this.bind_events();
    };


    Pager.prototype.style = function () {
        this.pager_splitter_element.addClass('border-box-sizing ui-widget ui-state-default');
        this.pager_element.addClass('border-box-sizing ui-widget');
    };


    Pager.prototype.bind_events = function () {
        var that = this;

        this.pager_element.bind('collapse_pager', function () {
            that.pager_element.hide('fast');
        });

        this.pager_element.bind('expand_pager', function () {
            that.pager_element.show('fast');
        });

        this.pager_splitter_element.hover(
            function () {
                that.pager_splitter_element.addClass('ui-state-hover');
            },
            function () {
                that.pager_splitter_element.removeClass('ui-state-hover');
            }
        );

        this.pager_splitter_element.click(function () {
            that.toggle();
        });

    };


    Pager.prototype.collapse = function () {
        if (this.expanded === true) {
            this.pager_element.add($('div#notebook')).trigger('collapse_pager');
            this.expanded = false;
        };
    };


    Pager.prototype.expand = function () {
        if (this.expanded !== true) {
            this.pager_element.add($('div#notebook')).trigger('expand_pager');
            this.expanded = true;
        };
    };


    Pager.prototype.toggle = function () {
        if (this.expanded === true) {
            this.collapse();
        } else {
            this.expand();
        };
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

