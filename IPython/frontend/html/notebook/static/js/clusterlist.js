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
        $('div#cluster_header').addClass('list_header ui-widget ui-widget-header');
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
        console.log(data);
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var item_div = $('<div/>');
            item_div.addClass('list_item ui-widget ui-widget-content ui-helper-clearfix');
            item_div.css('border-top-style','none');
            var item = new ClusterItem(item_div);
            item.update_state(data[i]);
            item_div.data('item', item);
            console.log('appending item', item);
            this.element.append(item_div);
        };
    };


    var ClusterItem = function (element) {
        this.element = $(element);
        this.data = null;
    };


    ClusterItem.prototype.update_state = function (data) {
        this.data = data;
        if (data.status === 'running') {
            this.state_running();
        } else if (data.status === 'stopped') {
            this.state_stopped();
        };

    }


    ClusterItem.prototype.state_stopped = function () {
        var item_name = $('<span/>').addClass('item_name').text(this.data.profile);
        var item_buttons = $('<span/>').addClass('item_buttons');
        var start_button = $('<button>Start</button>').button();
        item_buttons.append(start_button);
        this.element.append(item_name).append(item_buttons);
        start_button.click(function (e) {
            console.log('start');
        });
    }


    ClusterItem.prototype.start_success = function () {
        
    };

    ClusterItem.prototype.state_running = function () {
        var item_name = $('<span/>').addClass('item_name').text(this.data.profile);
        var item_buttons = $('<span/>').addClass('item_buttons');
        var stop_button = $('<button>Stop</button>').button();
        item_buttons.append(start_button);
        this.element.append(item_name).append(item_buttons);
        start_button.click(function (e) {
            console.log('stop');
        });
    };


    IPython.ClusterList = ClusterList;
    IPython.ClusterItem = ClusterItem;

    return IPython;

}(IPython));

