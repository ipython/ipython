//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Login button
//============================================================================

var IPython = (function (IPython) {
    var base_url = $('body').data('baseProjectUrl');

    var LoginWidget = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    LoginWidget.prototype.style = function () {
        this.element.find('button#logout').button();
        this.element.find('button#login').button();
    };


    LoginWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find("button#logout").click(function () {
            window.location = base_url+"logout";
        });
        this.element.find("button#login").click(function () {
            window.location = base_url+"login";
        });
    };

    // Set module variables
    IPython.LoginWidget = LoginWidget;

    return IPython;

}(IPython));
