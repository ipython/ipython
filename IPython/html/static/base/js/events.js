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
    
    // Backwards compatability.
    IPython.Events = Events;
    
    return {'Events': Events};
});
