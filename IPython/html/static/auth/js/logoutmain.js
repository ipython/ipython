// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require(['base/js/namespace', 'base/js/page'], function(IPython, Page) {
    IPython.page = new Page();
    $('#ipython-main-app').addClass('border-box-sizing');
    IPython.page.show();
});
