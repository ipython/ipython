// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/keyboard',
    'notebook/js/celltoolbar',
    'bootstraptags',
], function($, keyboard, celltoolbar, bootstrap_tags) {
    "use strict";

    var register = function (notebook) {
        // Register the cell tagging toolbar.

        console.log('Cell tags extension loaded.');
    };

    return {'register': register};
});