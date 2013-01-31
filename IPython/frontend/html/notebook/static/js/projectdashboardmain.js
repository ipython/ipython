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
    $('div#tabs').on('tabsselect', function (event, ui) {
        var new_url = $('body').data('baseProjectUrl') + '#' + ui.panel.id;
        window.history.replaceState({}, '', new_url);
    });
    $('#ipython-main-app').addClass('border-box-sizing ui-widget');
    $('div#notebooks_toolbar').addClass('ui-widget ui-helper-clearfix');    
    $('#new_notebook').button().click(function (e) {
        window.open($('body').data('baseProjectUrl')+'new');
    });

    IPython.read_only = $('body').data('readOnly') === 'True';
    IPython.notebook_list = new IPython.NotebookList('div#notebook_list');
    IPython.cluster_list = new IPython.ClusterList('div#cluster_list');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');

    var interval_id=0;
    // auto refresh every xx secondes, no need to be fast,
    //  update is done at least when page get focus
    var time_refresh = 60; // in sec

    var enable_autorefresh = function(){
        //refresh immediately , then start interval
        if($('.upload_button').length == 0)
        {
            IPython.notebook_list.load_list();
            IPython.cluster_list.load_list();
        }
        if (!interval_id){
            interval_id = setInterval(function(){
                    if($('.upload_button').length == 0)
                    {
                        IPython.notebook_list.load_list();
                        IPython.cluster_list.load_list();
                    }
                }, time_refresh*1000);
            }
    }

    var disable_autorefresh = function(){
        clearInterval(interval_id);
        interval_id = 0;
    }

    // stop autorefresh when page lose focus
    $(window).blur(function() {
        disable_autorefresh();
    })

    //re-enable when page get focus back
    $(window).focus(function() {
        enable_autorefresh();
    });

    // finally start it, it will refresh immediately
    enable_autorefresh();

    IPython.page.show();
    
    // bound the upload method to the on change of the file select list
    $("#alternate_upload").change(function (event){
        IPython.notebook_list.handelFilesUpload(event,'form');
    });

});

