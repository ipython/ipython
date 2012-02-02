//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Events
//============================================================================

// Give us an object to bind all events to. This object should be created
// before all other objects so it exists when others register event handlers.
// To trigger an event handler:
// $([IPython.events]).trigger('event.Namespace);
// To handle it:
// $([IPython.events]).on('event.Namespace',function () {});

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Events = function () {};

    IPython.Events = Events;
    IPython.events = new Events();

    return IPython;

}(IPython));

