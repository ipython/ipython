//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Hooks
//============================================================================
// extend jQuerry

// same function as jQuerry Event .trigger, but catch exeption and log the message that have raised.
// return null if have raised.
$.fn.safe_trigger = function (eventType, extraParameters){
    try {
        return $(this).trigger(eventType, extraParameters)
    }
    catch(err) {
        console.log('event "'+String(eventType)+'" have raised');
        return null
    }
}

// same version as above, but "non-blocking" or "Asynchrone"
// whatever you called it, it return imediately as Qt .emit()
$.fn.async_trigger = function (eventType, extraParameters){
        that = this;
        setTimeout(function(){$(that).safe_trigger(eventType, extraParameters)},0);
}

// We REALLY nead an early object to bind event
var IPython = (function (IPython) {
    IPython.hook = new Object();
    return IPython;
}(IPython));

