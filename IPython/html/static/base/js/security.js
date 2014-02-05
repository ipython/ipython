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

    var is_safe = function (html) {
        // Is the html string safe against JavaScript based attacks. This
        // detects 1) black listed tags, 2) blacklisted attributes, 3) all
        // event attributes (onhover, onclick, etc.).
        var black_tags = ['script', 'style', 'meta', 'iframe', 'embed'];
        var black_attrs = ['style'];
        var wrapped_html = '<div>'+html+'</div>';
        // First try to parse the HTML. All invalid HTML is unsafe.
        try {
            var bad_elem = $(wrapped_html);
        } catch (e) {
            return false;
        }
        var safe = true;
        // Detect black listed tags
        $.map(black_tags, function (tag, index) {
            if (bad_elem.find(tag).length > 0) {
                safe = false;
            }
        });
        // Detect black listed attributes
        $.map(black_attrs, function (attr, index) {
            if (bad_elem.find('['+attr+']').length > 0) {
                safe = false;
            }
        });
        bad_elem.find('*').each(function (index) {
            $.map(utils.get_attr_names($(this)), function (attr, index) {
                if (attr.match('^on')) {safe = false;}
            });
        })
        return safe;
    }

    return {
        is_safe: is_safe
    };

}(IPython));

