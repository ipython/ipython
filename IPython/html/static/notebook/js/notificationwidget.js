// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
], function(IPython, $) {
    "use strict";

    var NotificationWidget = function (selector) {
        this.selector = selector;
        this.timeout = null;
        this.busy = false;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
        this.element.hide();
        this.inner = $('<span/>');
        this.element.append(this.inner);
    };

    NotificationWidget.prototype.style = function () {
        this.element.addClass('notification_widget');
    };

    // msg : message to display
    // timeout : time in ms before diseapearing
    //
    // if timeout <= 0
    // click_callback : function called if user click on notification
    // could return false to prevent the notification to be dismissed
    NotificationWidget.prototype.set_message = function (msg, timeout, click_callback, options) {
        options = options || {};

        // unbind potential previous callback
        this.element.unbind('click');
        this.inner.attr('class', options.icon);
        this.inner.attr('title', options.title);
        this.inner.text(msg);
        this.element.fadeIn(100);

        // reset previous set style
        this.element.removeClass();
        this.style();
        if (options.class){
            this.element.addClass(options.class);
        }

        // clear previous timer
        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }

        // set the timer if a timeout is given
        var that = this;
        if (timeout !== undefined && timeout >= 0) {
            this.timeout = setTimeout(function () {
                that.element.fadeOut(100, function () {that.inner.text('');});
                that.element.unbind('click');
                that.timeout = null;
            }, timeout);
        }

        // bind the click callback if it is given
        if (click_callback !== undefined) {
            this.element.click(function() {
                if (click_callback() !== false) {
                    that.element.fadeOut(100, function () {that.inner.text('');});
                    that.element.unbind('click');
                }
                if (that.timeout !== null) {
                    clearTimeout(that.timeout);
                    that.timeout = null;
                }
            });
        }
    };

    NotificationWidget.prototype.info = function (msg, timeout, click_callback, options) {
        options = options || {};
        options.class = options.class + ' info';
        timeout = timeout || 3500;
        this.set_message(msg, timeout, click_callback, options);
    };

    NotificationWidget.prototype.warning = function (msg, timeout, click_callback, options) {
        options = options || {};
        options.class = options.class + ' warning';
        this.set_message(msg, timeout, click_callback, options);
    };

    NotificationWidget.prototype.danger = function (msg, timeout, click_callback, options) {
        options = options || {};
        options.class = options.class + ' danger';
        this.set_message(msg, timeout, click_callback, options);
    };

    NotificationWidget.prototype.get_message = function () {
        return this.inner.html();
    };

    // For backwards compatibility.
    IPython.NotificationWidget = NotificationWidget;

    return {'NotificationWidget': NotificationWidget};
});
