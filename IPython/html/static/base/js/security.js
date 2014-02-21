//----------------------------------------------------------------------------
//  Copyright (C) 2014  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Utilities
//============================================================================
IPython.namespace('IPython.security');

IPython.security = (function (IPython) {
    "use strict";

    var utils = IPython.utils;
    
    var noop = function (x) { return x; };
    
    var cmp_tree = function (a, b) {
        // compare two HTML trees
        // only checks the tag structure is preserved,
        // not any attributes or contents
        if (a.length !== b.length) {
            return false;
        }
        
        for (var i = a.length - 1; i >= 0; i--) {
            if (a[i].tagName && b[i].tagName && a[i].tagName.toLowerCase() != b[i].tagName.toLowerCase()) {
                return false;
            }
        }
        var ac = a.children();
        var bc = b.children();
        if (ac.length === 0 && bc.length === 0) {
            return true;
        }
        return cmp_tree(ac, bc);
    };
    
    var sanitize = function (html, log) {
        // sanitize HTML
        // returns a struct of
        // {
        //   src: original_html,
        //   sanitized: the_sanitized_html,
        //   safe: bool // false if the sanitizer made any changes
        // }
        var result = {
            src : html,
            safe : true
        };
        var record_messages = function (msg, opts) {
            console.log("HTML Sanitizer", msg, opts);
            result.safe = false;
        };
        result.sanitized = window.html_sanitize(html, noop, noop, record_messages);
        // caja can strip whole elements without logging,
        // so double-check that node structure didn't change
        if (result.safe) {
            result.safe = cmp_tree($(result.sanitized), $(result.src));
        }
        return result;
    };
    
    var sanitize_html = function (html) {
        // shorthand for str-to-str conversion, dropping the struct
        return sanitize(html).sanitized;
    };
    
    var is_safe = function (html) {
        // just return bool for whether an HTML string is safe
        return sanitize(html).safe;
    };
    
    return {
        is_safe: is_safe,
        sanitize: sanitize,
        sanitize_html: sanitize_html
    };

}(IPython));

