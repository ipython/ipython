// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

// Give us an object to bind all events to. This object should be created
// before all other objects so it exists when others register event handlers.
// To trigger an event handler:
// $([IPython.events]).trigger('event.Namespace');
// To handle it:
// $([IPython.events]).on('event.Namespace',function () {});
define(['base/js/namespace'], function(IPython) {
    "use strict";

    var Events = function () {};
    events = new Events();

    // Backwards compatability.
    IPython.Events = Events;
    IPython.events = events;

    // This behavior is an akward exception to the normal design pattern of 
    // returning the namespace.  Events are used eveywhere in IPython,
    // and only one instance is ever used.  For convenience, create and
    // return that instance here instead of the namespace.
    return events;
});
