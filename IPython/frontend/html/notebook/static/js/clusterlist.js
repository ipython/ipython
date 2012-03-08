//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// NotebookList
//============================================================================

var IPython = (function (IPython) {

    var ClusterList = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
    };

    ClusterList.prototype.style = function () {
        $('#cluster_toolbar').addClass('list_toolbar');
        $('#cluster_list_info').addClass('toolbar_info');
        $('#cluster_buttons').addClass('toolbar_buttons');
        $('div#cluster_header').addClass('list_header ui-widget ui-widget-header ui-helper-clearfix');
        $('div#cluster_header').children().eq(0).addClass('profile_col');
        $('div#cluster_header').children().eq(1).addClass('action_col');
        $('div#cluster_header').children().eq(2).addClass('engines_col');
        $('div#cluster_header').children().eq(3).addClass('status_col');
        $('#refresh_cluster_list').button({
            icons : {primary: 'ui-icon-arrowrefresh-1-s'},
            text : false
        });
    };


    ClusterList.prototype.bind_events = function () {
        var that = this;
        $('#refresh_cluster_list').click(function () {
            that.load_list();
        });
    };


    ClusterList.prototype.load_list = function () {
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.load_list_success, this)
        };
        var url = $('body').data('baseProjectUrl') + 'clusters';
        $.ajax(url, settings);
    };


    ClusterList.prototype.clear_list = function () {
        this.element.children('.list_item').remove();
    }

    ClusterList.prototype.load_list_success = function (data, status, xhr) {
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var item_div = $('<div/>');
            var item = new ClusterItem(item_div);
            item.update_state(data[i]);
            item_div.data('item', item);
            this.element.append(item_div);
        };
    };


    var ClusterItem = function (element) {
        this.element = $(element);
        this.data = null;
        this.style();
    };


    ClusterItem.prototype.style = function () {
        this.element.addClass('list_item ui-widget ui-widget-content ui-helper-clearfix');
        this.element.css('border-top-style','none');
    }

    ClusterItem.prototype.update_state = function (data) {
        this.data = data;
        if (data.status === 'running') {
            this.state_running();
        } else if (data.status === 'stopped') {
            this.state_stopped();
        };

    }


    ClusterItem.prototype.state_stopped = function () {
        var that = this;
        this.element.empty();
        var profile_col = $('<span/>').addClass('profile_col').text(this.data.profile);
        var status_col = $('<span/>').addClass('status_col').html('stopped');
        var engines_col = $('<span/>').addClass('engines_col');
        var input = $('<input/>').attr('type','text').
                attr('size',3).addClass('engine_num_input');
        engines_col.append(input);
        var action_col = $('<span/>').addClass('action_col');
        var start_button = $('<button>Start</button>').button();
        action_col.append(start_button);
        this.element.append(profile_col).
            append(action_col).
            append(engines_col).
            append(status_col);
        start_button.click(function (e) {
            var n = that.element.find('.engine_num_input').val();
            if (!/^\d+$/.test(n) && n.length>0) {
                status_col.html('invalid engine #');
            } else {
                var settings = {
                    cache : false,
                    data : {n:n},
                    type : "POST",
                    dataType : "json",
                    success : function (data, status, xhr) {
                        that.update_state(data);
                    },
                    error : function (data, status, xhr) {
                        status_col.html("error starting cluster")
                    }
                };
                status_col.html('starting');
                var url = $('body').data('baseProjectUrl') + 'clusters/' + that.data.profile + '/start';
                $.ajax(url, settings);
            };
        });
    };


    ClusterItem.prototype.state_running = function () {
        this.element.empty();
        var that = this;
        var profile_col = $('<span/>').addClass('profile_col').text(this.data.profile);
        var status_col = $('<span/>').addClass('status_col').html('running');
        var engines_col = $('<span/>').addClass('engines_col').html(this.data.n);
        var action_col = $('<span/>').addClass('action_col');
        var stop_button = $('<button>Stop</button>').button();
        action_col.append(stop_button);
        this.element.append(profile_col).
            append(action_col).
            append(engines_col).
            append(status_col);
        stop_button.click(function (e) {
            var settings = {
                cache : false,
                type : "POST",
                dataType : "json",
                success : function (data, status, xhr) {
                    that.update_state(data);
                },
                error : function (data, status, xhr) {
                    console.log('error',data);
                    status_col.html("error stopping cluster")
                }
            };
            status_col.html('stopping')
            var url = $('body').data('baseProjectUrl') + 'clusters/' + that.data.profile + '/stop';
            $.ajax(url, settings);
        });
    };


    IPython.ClusterList = ClusterList;
    IPython.ClusterItem = ClusterItem;

    return IPython;

}(IPython));

