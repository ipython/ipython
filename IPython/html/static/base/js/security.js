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
    
    var caja;
    if (window && window.html) {
        caja = window.html;
        caja.html4 = window.html4;
        caja.sanitizeStylesheet = window.sanitizeStylesheet;
    }
    
    var sanitizeAttribs = function (tagName, attribs, opt_naiveUriRewriter, opt_nmTokenPolicy, opt_logger) {
        // add trusting data-attributes to the default sanitizeAttribs from caja
        // this function is mostly copied from the caja source
        var ATTRIBS = caja.html4.ATTRIBS;
        for (var i = 0; i < attribs.length; i += 2) {
            var attribName = attribs[i];
            if (attribName.substr(0,5) == 'data-') {
                var attribKey = '*::' + attribName;
                if (!ATTRIBS.hasOwnProperty(attribKey)) {
                    ATTRIBS[attribKey] = 0;
                }
            }
        }
        return caja.sanitizeAttribs(tagName, attribs, opt_naiveUriRewriter, opt_nmTokenPolicy, opt_logger);
    };
    
    var sanitize_css = function (css, tagPolicy) {
        // sanitize CSS
        // like sanitize_html, but for CSS
        // called by sanitize_stylesheets
        return caja.sanitizeStylesheet(
            window.location.pathname,
            css,
            {
                containerClass: null,
                idSuffix: '',
                tagPolicy: tagPolicy,
                virtualizeAttrName: noop
            },
            noop
        );
    };
    
    var sanitize_stylesheets = function (html, tagPolicy) {
        // sanitize just the css in style tags in a block of html
        // called by sanitize_html, if allow_css is true
        var h = $("<div/>").append(html);
        var style_tags = h.find("style");
        if (!style_tags.length) {
            // no style tags to sanitize
            return html;
        }
        style_tags.each(function(i, style) {
            style.innerHTML = sanitize_css(style.innerHTML, tagPolicy);
        });
        return h.html();
    };
    
    var sanitize_html = function (html, allow_css) {
        // sanitize HTML
        // if allow_css is true (default: false), CSS is sanitized as well.
        // otherwise, CSS elements and attributes are simply removed.
        var html4 = caja.html4;

        if (allow_css) {
            // allow sanitization of style tags,
            // not just scrubbing
            html4.ELEMENTS.style &= ~html4.eflags.UNSAFE;
            html4.ATTRIBS.style = html4.atype.STYLE;
        } else {
            // scrub all CSS
            html4.ELEMENTS.style |= html4.eflags.UNSAFE;
            html4.ATTRIBS.style = html4.atype.SCRIPT;
        }
        
        var record_messages = function (msg, opts) {
            console.log("HTML Sanitizer", msg, opts);
        };
        
        var policy = function (tagName, attribs) {
            if (!(html4.ELEMENTS[tagName] & html4.eflags.UNSAFE)) {
                return {
                    'attribs': sanitizeAttribs(tagName, attribs,
                        noop, noop, record_messages)
                    };
            } else {
                record_messages(tagName + " removed", {
                  change: "removed",
                  tagName: tagName
                });
            }
        };
        
        var sanitized = caja.sanitizeWithPolicy(html, policy);
        
        if (allow_css) {
            // sanitize style tags as stylesheets
            sanitized = sanitize_stylesheets(result.sanitized, policy);
        }
        
        return sanitized;
    };
    
    return {
        caja: caja,
        sanitize_html: sanitize_html
    };

}(IPython));

