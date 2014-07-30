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
        var that = this;

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
        var options = options || {};
        var callback = click_callback || function() {return true;};
        var that = this;
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

            this.element.addClass(options.class)
        }
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


    NotificationWidget.prototype.info = function (msg, timeout, click_callback, options) {
        var options = options || {};
        options.class = options.class +' info';
        var timeout = timeout || 3500;
        this.set_message(msg, timeout, click_callback, options);
    }
    NotificationWidget.prototype.warning = function (msg, timeout, click_callback, options) {
        var options = options || {};
        options.class = options.class +' warning';
        this.set_message(msg, timeout, click_callback, options);
    }
    NotificationWidget.prototype.danger = function (msg, timeout, click_callback, options) {
        var options = options || {};
        options.class = options.class +' danger';
        this.set_message(msg, timeout, click_callback, options);
    }


    NotificationWidget.prototype.get_message = function () {
        return this.inner.html();
    };

    // For backwards compatibility.
    IPython.NotificationWidget = NotificationWidget;

    return {'NotificationWidget': NotificationWidget};
});
