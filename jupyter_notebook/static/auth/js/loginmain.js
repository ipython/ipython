// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

var ipython = ipython || {};
require(['base/js/page'], function(page) {
    var page_instance = new page.Page();
    $('button#login_submit').addClass("btn btn-default");
    page_instance.show();
    $('input#password_input').focus();
    
    ipython.page = page_instance;
});
