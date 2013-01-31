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
    $('input#login_submit').button();
    $('#ipython-main-app').addClass('border-box-sizing ui-widget');
    IPython.page.show();
    $('input#password_input').focus();

});

