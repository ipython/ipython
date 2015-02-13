// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/namespace',
    'base/js/dialog',
    'base/js/events',
    'base/js/page',
    'base/js/utils',
    'services/config',
    'contents',
    'tree/js/notebooklist',
    'tree/js/clusterlist',
    'tree/js/sessionlist',
    'tree/js/kernellist',
    'tree/js/terminallist',
    'tree/js/newnotebook',
    'auth/js/loginwidget',
    // only loaded, not used:
    'jqueryui',
    'bootstrap',
    'custom/custom',
], function(
    $,
    IPython,
    dialog,
    events,
    page,
    utils,
    config,
    contents_service,
    notebooklist,
    clusterlist,
    sesssionlist,
    kernellist,
    terminallist,
    newnotebook,
    loginwidget){
    "use strict";

    page = new page.Page();
    
    var common_options = {
        base_url: utils.get_body_data("baseUrl"),
        notebook_path: utils.get_body_data("notebookPath"),
    };
    var cfg = new config.ConfigSection('tree', common_options);
    cfg.load();
    common_options.config = cfg;
    var common_config = new config.ConfigSection('common', common_options);
    common_config.load();

    var session_list = new sesssionlist.SesssionList($.extend({
        events: events},
        common_options));
    var contents = new contents_service.Contents({
        base_url: common_options.base_url,
        common_config: common_config
    });
    var notebook_list = new notebooklist.NotebookList('#notebook_list', $.extend({
        contents: contents,
        session_list:  session_list}, 
        common_options));
    var cluster_list = new clusterlist.ClusterList('#cluster_list', common_options);
    var kernel_list = new kernellist.KernelList('#running_list',  $.extend({
        session_list:  session_list}, 
        common_options));
    
    var terminal_list;
    if (utils.get_body_data("terminalsAvailable") === "True") {
        terminal_list = new terminallist.TerminalList('#terminal_list', common_options);
    }

    var login_widget = new loginwidget.LoginWidget('#login_widget', common_options);

    var new_buttons = new newnotebook.NewNotebookWidget("#new-buttons",
        $.extend(
            {contents: contents},
            common_options
        )
    );

    var interval_id=0;
    // auto refresh every xx secondes, no need to be fast,
    //  update is done most of the time when page get focus
    IPython.tree_time_refresh = 60; // in sec

    // limit refresh on focus at 1/10sec, otherwise this
    // can cause too frequent refresh on switching through windows or tabs.
    IPython.min_delta_refresh = 10; // in sec

    var _last_refresh = null;

    var _refresh_list = function(){
        _last_refresh = new Date();
        session_list.load_sessions();
        cluster_list.load_list();
        if (terminal_list) {
            terminal_list.load_terminals();
        }
    };

    var enable_autorefresh = function(){
        /**
         *refresh immediately , then start interval
         */
        var now = new Date();

        if (now - _last_refresh < IPython.min_delta_refresh*1000){
            console.log("Reenabling autorefresh too close to last tree refresh, not refreshing immediately again.");
        } else {
            _refresh_list();
        }
        if (!interval_id){
            interval_id = setInterval(_refresh_list,
                    IPython.tree_time_refresh*1000
            );
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
    IPython.new_notebook_widget = new_buttons;

    events.trigger('app_initialized.DashboardApp');
    utils.load_extensions_from_config(cfg);
    utils.load_extensions_from_config(common_config);
    
    // bound the upload method to the on change of the file select list
    $("#alternate_upload").change(function (event){
        notebook_list.handleFilesUpload(event,'form');
    });
    
    // set hash on tab click
    $("#tabs").find("a").click(function(e) {
        // Prevent the document from jumping when the active tab is changed to a 
        // tab that has a lot of content.
        e.preventDefault();

        // Set the hash without causing the page to jump.
        // http://stackoverflow.com/a/14690177/2824256
        var hash = $(this).attr("href");
        if(window.history.pushState) {
            window.history.pushState(null, null, hash);
        } else {
            window.location.hash = hash;
        }
    });
    
    // load tab if url hash
    if (window.location.hash) {
        $("#tabs").find("a[href=" + window.location.hash + "]").click();
    }
});
