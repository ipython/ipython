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

