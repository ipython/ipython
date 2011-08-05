
//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {

    $('div#header').addClass('border-box-sizing');
    $('div#header_border').addClass('border-box-sizing ui-widget ui-widget-content');

    $('div#main_app').addClass('border-box-sizing ui-widget');
    $('div#app_hbox').addClass('hbox center');

    $('div#content_toolbar').addClass('ui-widget ui-helper-clearfix');    

    $('#new_notebook').click(function (e) {
        window.open('/new');
    });

    IPython.notebook_list = new IPython.NotebookList('div#notebook_list');
    IPython.notebook_list.load_list();

    // These have display: none in the css file and are made visible here to prevent FLOUC.
    $('div#header').css('display','block');
    $('div#main_app').css('display','block');


});

