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

    ClusterList.prototype.baseProjectUrl = function(){
        return this._baseProjectUrl || $('body').data('baseProjectUrl');
    };

    ClusterList.prototype.style = function () {
        $('#cluster_list').addClass('list_container');
        $('#cluster_toolbar').addClass('list_toolbar');
        $('#cluster_list_info').addClass('toolbar_info');
        $('#cluster_buttons').addClass('toolbar_buttons');
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
        var url = this.baseProjectUrl() + 'clusters';
        $.ajax(url, settings);
    };


    ClusterList.prototype.clear_list = function () {
        this.element.children('.list_item').remove();
    }

    ClusterList.prototype.load_list_success = function (data, status, xhr) {
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var element = $('<div/>');
            var item = new ClusterItem(element);
            item.update_state(data[i]);
            element.data('item', item);
            this.element.append(element);
        };
    };


    var ClusterItem = function (element) {
        this.element = $(element);
        this.data = null;
        this.style();
    };

    ClusterItem.prototype.baseProjectUrl = function(){
        return this._baseProjectUrl || $('body').data('baseProjectUrl');
    };



    ClusterItem.prototype.style = function () {
        this.element.addClass('list_item').addClass("row-fluid");
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
        var profile_col = $('<span/>').addClass('profile_col span4').text(this.data.profile);
        var status_col = $('<span/>').addClass('status_col span3').html('stopped');
        var engines_col = $('<span/>').addClass('engine_col span3');
        var input = $('<input/>').attr('type','number')
                .attr('min',1)
                .attr('size',3)
                .addClass('engine_num_input');
        engines_col.append(input);
        var start_button = $('<button/>').addClass("btn btn-mini").text("Start");
        var action_col = $('<span/>').addClass('action_col span2').append(
            $("<span/>").addClass("item_buttons btn-group").append(
                start_button
            )
        );
        this.element.empty()
            .append(profile_col)
            .append(status_col)
            .append(engines_col)
            .append(action_col);
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
                var url = that.baseProjectUrl() + 'clusters/' + that.data.profile + '/start';
                $.ajax(url, settings);
            };
        });
    };


    ClusterItem.prototype.state_running = function () {
        var that = this;
        var profile_col = $('<span/>').addClass('profile_col span4').text(this.data.profile);
        var status_col = $('<span/>').addClass('status_col span3').html('running');
        var engines_col = $('<span/>').addClass('engines_col span3').html(this.data.n);
        var stop_button = $('<button/>').addClass("btn btn-mini").text("Stop");
        var action_col = $('<span/>').addClass('action_col span2').append(
            $("<span/>").addClass("item_buttons btn-group").append(
                stop_button
            )
        );
        this.element.empty()
            .append(profile_col)
            .append(status_col)
            .append(engines_col)
            .append(action_col);
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
            var url = that.baseProjectUrl() + 'clusters/' + that.data.profile + '/stop';
            $.ajax(url, settings);
        });
    };


    IPython.ClusterList = ClusterList;
    IPython.ClusterItem = ClusterItem;

    return IPython;

}(IPython));

