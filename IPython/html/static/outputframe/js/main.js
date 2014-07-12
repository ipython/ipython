// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'base/js/namespace',
    'jquery',
    'outputframe/js/outputarea'
], function(
    IPython, 
    $,
    outputarea
    ) {
    "use strict";

    var element = $('#output_frame')
    var output_area = new outputarea.OutputArea(element);

});
