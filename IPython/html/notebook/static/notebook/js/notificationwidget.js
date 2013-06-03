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
    "use strict";
    var utils = IPython.utils;


    var NotificationWidget = function (selector) {
        this.selector = selector;
        this.timeout = null;
        this.busy = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
        this.element.button();
        this.element.hide();
        var that = this;

    };


    NotificationWidget.prototype.style = function () {
        this.element.addClass('notification_widget pull-right');
        this.element.addClass('border-box-sizing');
    };

    // msg : message to display
    // timeout : time in ms before diseapearing
    //
    // if timeout <= 0
    // click_callback : function called if user click on notification
    // could return false to prevent the notification to be dismissed
    NotificationWidget.prototype.set_message = function (msg, timeout, click_callback) {
        var callback = click_callback || function() {return false;};
        var that = this;
        this.element.html(msg);
        this.element.fadeIn(100);
        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
        if (timeout !== undefined && timeout >=0) {
            this.timeout = setTimeout(function () {
                that.element.fadeOut(100, function () {that.element.html('');});
                that.timeout = null;
            }, timeout);
        } else {
            this.element.click(function() {
                if( callback() != false ) {
                    that.element.fadeOut(100, function () {that.element.html('');});
                    that.element.unbind('click');
                }
                if (that.timeout !== undefined) {
                    that.timeout = undefined;
                    clearTimeout(that.timeout);
                }
            });
        }
    };


    NotificationWidget.prototype.get_message = function () {
        return this.element.html();
    };


    IPython.NotificationWidget = NotificationWidget;

    return IPython;

}(IPython));

