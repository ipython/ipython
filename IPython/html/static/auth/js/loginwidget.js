// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'base/js/utils',
    'components/jquery/jquery.min',
], function(IPython, Utils, $){
    "use strict";

    var LoginWidget = function (selector, options) {
        options = options || {};
        this.base_url = options.base_url || Utils.get_body_data("baseUrl");
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    LoginWidget.prototype.style = function () {
        this.element.find("button").addClass("btn btn-default btn-sm");
    };


    LoginWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find("button#logout").click(function () {
            window.location = Utils.url_join_encode(
                that.base_url,
                "logout"
            );
        });
        this.element.find("button#login").click(function () {
            window.location = Utils.url_join_encode(
                that.base_url,
                "login"
            );
        });
    };

    // Set module variables
    IPython.LoginWidget = LoginWidget;

    return LoginWidget;
});