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

    var LoginWidget = function (selector, options) {
        var options = options || {};
        this.base_url = options.baseProjectUrl || $('body').data('baseProjectUrl') ;
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    LoginWidget.prototype.style = function () {
        this.element.find("button").addClass("btn btn-small");
    };


    LoginWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find("button#logout").click(function () {
            window.location = that.base_url+"logout";
        });
        this.element.find("button#login").click(function () {
            window.location = that.base_url+"login";
        });
    };

    // Set module variables
    IPython.LoginWidget = LoginWidget;

    return IPython;

}(IPython));
