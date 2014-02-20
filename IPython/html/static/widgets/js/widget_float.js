//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// FloatWidget
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["widgets/js/widget", 
    "widgets/js/widget_int"], 
        function(WidgetManager, int_widgets){

    var IntSliderView = int_widgets[0];
    var IntTextView = int_widgets[1];


    var FloatSliderView = IntSliderView.extend({
        _validate_slide_value: function(x) {
            // Validate the value of the slider before sending it to the back-end
            // and applying it to the other views on the page.
            return x;
        },
    });
    WidgetManager.register_widget_view('FloatSliderView', FloatSliderView);


    var FloatTextView = IntTextView.extend({
        _parse_value: function(value) {
            // Parse the value stored in a string.
            return  parseFloat(value);
        },
    });
    WidgetManager.register_widget_view('FloatTextView', FloatTextView);
});
