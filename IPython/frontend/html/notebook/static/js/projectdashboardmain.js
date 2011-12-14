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

    $('div#header').addClass('border-box-sizing');
    $('div#header_border').addClass('border-box-sizing ui-widget ui-widget-content');

    $('div#main_app').addClass('border-box-sizing ui-widget');
    $('div#app_hbox').addClass('hbox');

    $('div#content_toolbar').addClass('ui-widget ui-helper-clearfix');    

    $('#new_notebook').button().click(function (e) {
        window.open($('body').data('baseProjectUrl')+'new');
    });

    $('div#left_panel').addClass('box-flex');
    $('div#right_panel').addClass('box-flex');

    IPython.read_only = $('meta[name=read_only]').attr("content") == 'True';
    IPython.notebook_list = new IPython.NotebookList('div#notebook_list');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');

    IPython.notebook_list.load_list();

    // These have display: none in the css file and are made visible here to prevent FLOUC.
    $('div#header').css('display','block');
    $('div#main_app').css('display','block');


});

