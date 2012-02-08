//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

    IPython.page = new IPython.Page();

    $('div#tabs').tabs();
    $('div#main_app').addClass('border-box-sizing ui-widget');
    $('div#notebooks_toolbar').addClass('ui-widget ui-helper-clearfix');    
    $('#new_notebook').button().click(function (e) {
        window.open($('body').data('baseProjectUrl')+'new');
    });

    IPython.read_only = $('body').data('readOnly') === 'True';
    IPython.notebook_list = new IPython.NotebookList('div#notebook_list');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');

    IPython.notebook_list.load_list();

    IPython.page.show();

});

