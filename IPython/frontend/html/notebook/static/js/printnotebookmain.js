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

    IPython.mathjaxutils.init();

    IPython.read_only = $('body').data('readOnly') === 'True';
    $('#ipython-main-app').addClass('border-box-sizing ui-widget');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');

    IPython.page = new IPython.Page();
    IPython.markdown_converter = new Markdown.Converter();
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');
    IPython.notebook = new IPython.Notebook('div#notebook');
    IPython.page.show_site();

    IPython.notebook.load_notebook($('body').data('notebookId'));

});

