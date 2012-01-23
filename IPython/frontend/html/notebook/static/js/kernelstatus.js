//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Kernel Status in title bar
//============================================================================

// basic connection, no object here : prepend busy to the window title if 'kernel_busy' emmited
$(IPython.hook).bind('kernel_busy',function(){window.document.title='(Busy) '+window.document.title});
$(IPython.hook).bind('kernel_restarting',function(){window.document.title='(Restarting) '+window.document.title});
//

// ask save_widget to reset document title on idle.  we use a lambda function
// here because save_widget is not yet defined when this file is loaded
$(IPython.hook).bind('kernel_idle',function(){IPython.save_widget.set_document_title()});

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
        var that=this;
        // Need to use anonymous function because connected function
        // are method of this object
        $(IPython.hook).bind("kernel_busy",function(){that.status_busy()})
        $(IPython.hook).bind("kernel_idle",function(){that.status_idle()})
        $(IPython.hook).bind("kernel_restarting",function(){that.status_restarting()})
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

IPython.kernel_status_widget = new IPython.KernelStatusWidget('#kernel_status');
