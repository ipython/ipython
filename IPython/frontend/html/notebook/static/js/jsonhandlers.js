//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// JSON Handlers
//============================================================================

var IPython = (function (IPython) {

    var JSONHandlers = function () {
        this.handlers = {};
    };


    JSONHandlers.prototype.register_handler = function(key, func) {
        this.handlers[key] = func
    };


    JSONHandlers.prototype.call_handler = function(key, json, element) {
        var handler = this.handlers[key]
        if (handler !== undefined) {
            try {
                handler(json, element);
            } catch(err) {
            };
        };
    };

    IPython.JSONHandlers = JSONHandlers

    return IPython;

}(IPython));
