
//============================================================================
// Kernel Status widget
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var KernelStatusWidget = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
    };


    KernelStatusWidget.prototype.style = function () {
        this.element.addClass('ui-widget');
    };


    KernelStatusWidget.prototype.status_busy = function () {
        this.element.removeClass("status_idle");
        this.element.removeClass("status_restarting");
        this.element.addClass("status_busy");
        this.element.text("Busy");
    };


    KernelStatusWidget.prototype.status_idle = function () {
        this.element.removeClass("status_busy");
        this.element.removeClass("status_restarting");
        this.element.addClass("status_idle");
        this.element.text("Idle");
    };

    KernelStatusWidget.prototype.status_restarting = function () {
        this.element.removeClass("status_busy");
        this.element.removeClass("status_idle");
        this.element.addClass("status_restarting");
        this.element.text("Restarting");
    };




    IPython.KernelStatusWidget = KernelStatusWidget;

    return IPython;

}(IPython));

