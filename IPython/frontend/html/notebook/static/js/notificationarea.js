//----------------------------------------------------------------------------
//  Copyright (C) 2012 The IPython Development Team
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


    var NotificationArea = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
        }
    };

    NotificationArea.prototype.temp_message = function (msg, timeout, css_class) {
        var uuid = utils.uuid();
        if( css_class == 'danger'){css_class = 'ui-state-error'}
        if( css_class == 'warning'){css_class = 'ui-state-highlight'}
        var tdiv = $('<div>')
            .attr('id',uuid)
            .addClass('notification ui-widget ui-widget-content ui-corner-all')
            .addClass('border-box-sizing')
            .addClass(css_class)
            .hide()
            .text(msg);

        $(this.selector).append(tdiv);
        var tmout = Math.max(1500,(timeout||1500));
        tdiv.fadeIn(100);

        setTimeout(function () {
                tdiv.fadeOut(100, function () {tdiv.remove();});
            }, tmout)
    };

    NotificationArea.prototype.new_notification_widget = function(name) {
        var div = $('<div/>').attr('id','notification_'+name);
        $(this.selector).append(div)
        return new IPython.NotificationWidget('#notification_'+name)
    }

    IPython.NotificationArea = NotificationArea;

    return IPython;

}(IPython));

