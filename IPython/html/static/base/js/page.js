// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/events',
], function(IPython, $, events){
    "use strict";

    var Page = function () {
        this.show_anchor_link();
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
        $('div#site').css('display', 'block');
    };
    

    Page.prototype.show_anchor_link = function() {
        /**
         * Scrolling to an anchor with a fixed header.
         * scroll_if_anchor is taken almost verbatim from http://jsfiddle.net/ianclark001/aShQL/.
         * Push state is not strictly necessary.
         * Note: Loading a URL with a fragment identifier works as expected. However, clicking on the address bar and pressing Enter again (without changing the fragment identifier) doesn't scroll correctly in Firefox. Firefox only follows the local links without reloading the document.
         */
        function scroll_if_anchor(href) {
            // Run only in /notebooks/
            var pathname = window.location.pathname;
            if (pathname.indexOf("/notebooks/") == 0) {

                var href = typeof(href) == "string" ? href : $(this).attr("href");
                
                // If our Href points to a valid, non-empty anchor, and is on the same page (e.g. #foo)
                // Legacy jQuery and IE7 may have issues: http://stackoverflow.com/q/1593174
                if(href.indexOf("#") == 0) {
                    var $target = $(href);
                    // Older browser without pushState might flicker here, as they momentarily
                    // jump to the wrong position (IE < 10)
                    if($target.length) {
                        $target[0].scrollIntoView();
                        if(history && "pushState" in history) {
                            history.pushState({}, document.title, window.location.pathname + href);
                            return false;
                        }
                    }
                }
            }
        }
        // When our page loads, check to see if it contains and anchor

        $(window).on('hashchange', function() {
            scroll_if_anchor(window.location.hash); 
        });
        // Intercept all anchor clicks in #site div
        $("#site").on("click", "a", scroll_if_anchor);

    }

    // Register self in the global namespace for convenience.
    IPython.Page = Page;
    return {'Page': Page};
});
