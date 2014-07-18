// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

var ipython = ipython || {};
require(['base/js/page'], function(page) {
    var page_instance = new page.Page();
    $('#ipython-main-app').addClass('border-box-sizing');
    page_instance.show();

    ipython.page = page_instance;
});
