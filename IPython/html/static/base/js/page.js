// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
], function(IPython, $){
    "use strict";

    var Page = function () {
        this.bind_events();
    };

    Page.prototype.bind_events = function () {
    };

    Page.prototype.show = function () {
        /**
         * The header and site divs start out hidden to prevent FLOUC.
         * Main scripts should call this method after styling everything.
         */
        this.show_header();
        this.show_site();
    };

    Page.prototype.show_header = function () {
        /**
         * The header and site divs start out hidden to prevent FLOUC.
         * Main scripts should call this method after styling everything.
         * TODO: selector are hardcoded, pass as constructor argument
         */
        $('div#header').css('display','block');
    };

    Page.prototype.show_site = function () {
        /**
         * The header and site divs start out hidden to prevent FLOUC.
         * Main scripts should call this method after styling everything.
         * TODO: selector are hardcoded, pass as constructor argument
         */
        $('div#site').css('display','block');
    };

    // Register self in the global namespace for convenience.
    IPython.Page = Page;
    return {'Page': Page};
});
