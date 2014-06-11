// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'components/jquery/jquery.min',
    'base/js/page',
    'base/js/utils',
    'tree/js/notebooklist',
    'tree/js/clusterlist',
    'tree/js/sessionlist',
    'tree/js/kernellist',
    'auth/js/loginwidget',
    'components/jquery-ui/ui/minified/jquery-ui.min',
    'components/bootstrap/js/bootstrap.min',
], function(
    IPython, 
    $, 
    Page, 
    Utils, 
    NotebookList, 
    ClusterList, 
    SesssionList, 
    KernelList, 
    LoginWidget){

    page = new Page();

    var opts = {
        base_url: Utils.get_body_data("baseUrl"),
        notebook_path: Utils.get_body_data("notebookPath"),
    };
    session_list = new SesssionList(opts);
    notebook_list = new NotebookList('#notebook_list', opts, undefined, session_list);
    cluster_list = new ClusterList('#cluster_list', opts);
    kernel_list = new KernelList('#running_list', opts, session_list);
    login_widget = new LoginWidget('#login_widget', opts);

    $('#new_notebook').button().click(function (e) {
        notebook_list.new_notebook();
    });
    
    var interval_id=0;
    // auto refresh every xx secondes, no need to be fast,
    //  update is done at least when page get focus
    var time_refresh = 60; // in sec

    var enable_autorefresh = function(){
        //refresh immediately , then start interval
        if($('.upload_button').length === 0)
        {
            session_list.load_sessions();
            cluster_list.load_list();
        }
        if (!interval_id){
            interval_id = setInterval(function(){
                    if($('.upload_button').length === 0)
                    {
                        session_list.load_sessions();
                        cluster_list.load_list();
                    }
                }, time_refresh*1000);
            }
    };

    var disable_autorefresh = function(){
        clearInterval(interval_id);
        interval_id = 0;
    };

    // stop autorefresh when page lose focus
    $(window).blur(function() {
        disable_autorefresh();
    });

    //re-enable when page get focus back
    $(window).focus(function() {
        enable_autorefresh();
    });

    // finally start it, it will refresh immediately
    enable_autorefresh();

    page.show();
    events.trigger('app_initialized.DashboardApp');
    
    // bound the upload method to the on change of the file select list
    $("#alternate_upload").change(function (event){
        notebook_list.handleFilesUpload(event,'form');
    });
    
    // set hash on tab click
    $("#tabs").find("a").click(function() {
        window.location.hash = $(this).attr("href");
    });
    
    // load tab if url hash
    if (window.location.hash) {
        $("#tabs").find("a[href=" + window.location.hash + "]").click();
    }

    // For backwards compatability.
    IPython.page = page;
    IPython.notebook_list = notebook_list;
    IPython.cluster_list = cluster_list;
    IPython.session_list = session_list;
    IPython.kernel_list = kernel_list;
    IPython.login_widget = login_widget;

    return page;
});
