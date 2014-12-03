// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "widgets/js/widget_int",
], function(widget, int_widgets){
    var IntSliderView = int_widgets.IntSliderView;
    var IntTextView = int_widgets.IntTextView;

    var FloatSliderView = IntSliderView.extend({
        _parse_value: parseFloat,

        // matches: whitespace?, float, whitespace?, [-:], whitespace?, float
        _range_regex: /^\s*([+-]?(?:\d*\.?\d+|\d+\.)(?:[eE][+-]?\d+)?)\s*[-:]\s*([+-]?(?:\d*\.?\d+|\d+\.)(?:[eE][+-]?\d+)?)/,

        _validate_slide_value: function(x) {
            /**
             * Validate the value of the slider before sending it to the back-end
             * and applying it to the other views on the page.
             */
            return x;
        },
    });

    var FloatTextView = IntTextView.extend({
        _parse_value: parseFloat
    });

    return {
        'FloatSliderView': FloatSliderView,
        'FloatTextView': FloatTextView,
    };
});
