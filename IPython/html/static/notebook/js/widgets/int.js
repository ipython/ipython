//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// IntWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["notebook/js/widget"], function(){
    var IntWidgetModel = IPython.WidgetModel.extend({});
    IPython.widget_manager.register_widget_model('IntWidgetModel', IntWidgetModel);
});