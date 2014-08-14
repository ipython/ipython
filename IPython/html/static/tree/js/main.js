// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'base/js/namespace',
    'jquery',
    'base/js/events',
    'base/js/page',
    'base/js/utils',
    'tree/js/notebooklist',
    'tree/js/clusterlist',
    'tree/js/sessionlist',
    'tree/js/kernellist',
    'auth/js/loginwidget',
    // only loaded, not used:
    'jqueryui',
    'bootstrap',
    'custom/custom',
], function(
    IPython, 
    $, 
    events,
    page, 
    utils, 
    notebooklist, 
    clusterlist, 
    sesssionlist, 
    kernellist, 
    loginwidget){

    page = new page.Page();
    
    var common_options = {
        base_url: utils.get_body_data("baseUrl"),
        notebook_path: utils.get_body_data("notebookPath"),
    };
    session_list = new sesssionlist.SesssionList($.extend({
        events: events}, 
        common_options));
    notebook_list = new notebooklist.NotebookList('#notebook_list', $.extend({
        session_list:  session_list}, 
        common_options));
    cluster_list = new clusterlist.ClusterList('#cluster_list', common_options);
    kernel_list = new kernellist.KernelList('#running_list',  $.extend({
        session_list:  session_list}, 
        common_options));
    login_widget = new loginwidget.LoginWidget('#login_widget', common_options);

    $('#new_notebook').click(function (e) {
        notebook_list.new_notebook();
    });

    var interval_id=0;
    // auto refresh every xx secondes, no need to be fast,
    //  update is done at least when page get focus
    var time_refresh = 60; // in sec

    var enable_autorefresh = function(){
        //refresh immediately , then start interval
        session_list.load_sessions();
        cluster_list.load_list();
        if (!interval_id){
            interval_id = setInterval(function(){
                    session_list.load_sessions();
                    cluster_list.load_list();
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

    // For backwards compatability.
    IPython.page = page;
    IPython.notebook_list = notebook_list;
    IPython.cluster_list = cluster_list;
    IPython.session_list = session_list;
    IPython.kernel_list = kernel_list;
    IPython.login_widget = login_widget;

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

});
