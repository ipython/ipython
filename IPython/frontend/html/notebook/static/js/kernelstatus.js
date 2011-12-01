//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

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
        this.element.attr('title', "The kernel execution status." +
        " If 'Busy', the kernel is currently running code." +
        " If 'Idle', it is available for execution.");
    };


    KernelStatusWidget.prototype.status_busy = function () {
        this.element.removeClass("status_idle");
        this.element.removeClass("status_restarting");
        this.element.addClass("status_busy");
        window.document.title='(Busy) '+window.document.title;
        this.element.text("Busy");
    };


    KernelStatusWidget.prototype.status_idle = function () {
        this.element.removeClass("status_busy");
        this.element.removeClass("status_restarting");
        this.element.addClass("status_idle");
        IPython.save_widget.set_document_title();
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

