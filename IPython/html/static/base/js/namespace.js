//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

var IPython = IPython || {};

IPython.version = "2.0.0";

IPython.namespace = function (ns_string) {
    "use strict";

    var parts = ns_string.split('.'),
        parent = IPython,
        i;

    // String redundant leading global
    if (parts[0] === "IPython") {
        parts = parts.slice(1);
    }

    for (i=0; i<parts.length; i+=1) {
        // Create property if it doesn't exist
        if (typeof parent[parts[i]] === "undefined") {
            parent[parts[i]] = {};
        }
    }
    return parent;
};



