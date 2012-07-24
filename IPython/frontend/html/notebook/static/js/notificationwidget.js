//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Notification widget
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;


    var NotificationWidget = function (selector) {
        this.selector = selector;
        this.timeout = null;
        this.busy = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            //this.bind_events();
        }
        this.element.button();
        this.element.hide();
        var that = this;
        this.element.click(function(){
            that.element.fadeOut(100, function () {that.element.html('');});
            if (that.timeout !== undefined) {
                that.timeout = undefined
                clearTimeout(that.timeout);
            }
        });
    };


    NotificationWidget.prototype.style = function () {
        this.element.addClass('notification ui-widget ui-widget-content ui-corner-all');
        this.element.addClass('border-box-sizing');
    };


    NotificationWidget.prototype.set_message = function (msg, timeout) {
        var that = this;
        this.element.html(msg);
        this.element.fadeIn(100);
        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        };
        if (timeout !== undefined && timeout >=0) {
            this.timeout = setTimeout(function () {
                that.element.fadeOut(100, function () {that.element.html('');});
                that.timeout = null;
            }, timeout);
        };
    };


    NotificationWidget.prototype.get_message = function () {
        return this.element.html();
    };


    IPython.NotificationWidget = NotificationWidget;

    return IPython;

}(IPython));

