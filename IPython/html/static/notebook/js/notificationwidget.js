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
        this.element.button();
        this.element.hide();
        var that = this;

        this.inner = $('<span/>');
        this.element.append(this.inner);

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
    NotificationWidget.prototype.set_message = function (msg, timeout, click_callback, options) {
        options = options || {};
        var callback = click_callback || function() {return false;};
        var that = this;
        this.inner.attr('class', options.icon);
        this.inner.attr('title', options.title);
        this.inner.text(msg);
        this.element.fadeIn(100);
        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
        if (timeout !== undefined && timeout >=0) {
            this.timeout = setTimeout(function () {
                that.element.fadeOut(100, function () {that.inner.text('');});
                that.timeout = null;
            }, timeout);
        } else {
            this.element.click(function() {
                if( callback() !== false ) {
                    that.element.fadeOut(100, function () {that.inner.text('');});
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
        return this.inner.html();
    };

    // For backwards compatability.
    IPython.NotificationWidget = NotificationWidget;

    return {'NotificationWidget': NotificationWidget};
});
