// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";

    var ClusterList = function (selector, options) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
        options = options || {};
        this.options = options;
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.notebook_path = options.notebook_path || utils.get_body_data("notebookPath");
        this.items = new Array();
        
        ClusterList.cluster_options_dialog = $('#cluster_options_dialog').dialog({
            width: 400,
            autoOpen: false,
            buttons: [
                {id:"cluster_options_start_button",text:"Start",click:function(){
                    $(this).dialog("close");
                }},
                {text:"Cancel",click:function(){$(this).dialog("close")}}
            ]
        });
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
            success : $.proxy(this.load_list_success, this),
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(this.base_url, 'clusters');
        $.ajax(url, settings);
    };


    ClusterList.prototype.clear_list = function () {
        this.items = new Array();
        this.element.children('.list_item').remove();
    };

    ClusterList.prototype.load_list_success = function (data, status, xhr) {
        this.clear_list();
        var len = data.length;
        for (var i=0; i<len; i++) {
            var element = $('<div/>');
            var item = new ClusterItem(element, this.options);
            this.items.push(item);
            item.update_state(data[i]);
            element.data('item', item);
            this.element.append(element);
        }
    };
    
    ClusterList.prototype.find_item = function (profile) {
        for (var i in this.items){
            if (this.items[i].data.profile == profile){
                return this.items[i];
            }
        }
    };


    var ClusterItem = function (element, options) {
        this.element = $(element);
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.notebook_path = options.notebook_path || utils.get_body_data("notebookPath");
        this.data = null;
        this.style();
    };

    ClusterItem.prototype.style = function () {
        this.element.addClass('list_item').addClass("row");
    };

    ClusterItem.prototype.update_state = function (data) {
        this.data = data;
        if (data.status === 'stopped') {
            this.state_stopped();
        } else {
            this.state_running();
        }
    };


    ClusterItem.prototype.state_stopped = function () {
        var that = this;
        var profile_col = $('<div/>').addClass('profile_col col-xs-4').text(this.data.profile);
        var status_col = $('<div/>').addClass('status_col col-xs-3').text('stopped');
        var engines_col = $('<div/>').addClass('engine_col col-xs-3');
        var input = $('<input/>').attr('type','number')
                .attr('min',1)
                .attr('size',3)
                .addClass('engine_num_input form-control');
        engines_col.append(input);
        var start_button = $('<button/>').addClass("btn btn-default btn-xs").text("Start");
        var options_button = $('<button/>').addClass("btn btn-default btn-xs").text("Options");
        var action_col = $('<div/>').addClass('action_col col-xs-2').append(
            $("<span/>").addClass("item_buttons pull-right").append(start_button)
        );
        if (that.data.batch){
            action_col.children('.item_buttons').append(options_button);
        }
        this.element.empty()
            .append(profile_col)
            .append(status_col)
            .append(engines_col)
            .append(action_col);
        this.start_engines = function(n, time, mem){
            if (!/^\d+$/.test(n) && n.length>0) {
                this.element.children('.status_col').text('invalid engine #');
            } else {
                var clusterItem = this;
                var settings = {
                    cache : false,
                    data : {n:n,time:time,mem:mem},
                    type : "POST",
                    dataType : "json",
                    success : function (data, status, xhr) {
                        clusterItem.update_state(data);
                    },
                    error : function (xhr, status, error) {
                        clusterItem.element.children('.status_col').text("error starting cluster");
                        utils.log_ajax_error(xhr, status, error);
                    }
                };
                this.element.children('.status_col').text('starting');
                var url = utils.url_join_encode(
                    this.base_url,
                    'clusters',
                    this.data.profile,
                    'start'
                );
                $.ajax(url, settings);
            }
        };
        start_button.click(function (e) {
            var n = that.element.find('.engine_num_input').val();
            that.start_engines(n);
        });
        options_button.click(function(e){
            ClusterList.cluster_options_dialog.dialog("open");
            $('#cluster_options_profile').text(that.data.profile);
            $('#cluster_options_start_button').unbind('click');
            $('#cluster_options_start_button').on('click', function(){
                var n = $('#cluster_options_engines').val();
                var time = $('#cluster_options_walltime').val();
                var mem = $('#cluster_options_mem').val();
                if (!$('#cluster_options_engines')[0].validity.valid){
                    $('#cluster_options_engines').focus();
                } else if (!$('#cluster_options_walltime')[0].validity.valid){
                    $('#cluster_options_walltime').focus();
                } else if (!$('#cluster_options_mem')[0].validity.valid){
                    $('#cluster_options_mem').focus();
                } else {
                    var item = IPython.cluster_list.find_item(that.data.profile)
                    item.start_engines(n,time,mem);
                    ClusterList.cluster_options_dialog.dialog('close');
                }
            });
        });
    };


    ClusterItem.prototype.state_running = function () {
        var that = this;
        var profile_col = $('<div/>').addClass('profile_col col-xs-4').text(this.data.profile);
        var status_col = $('<div/>').addClass('status_col col-xs-3').text(this.data.status);
        var engines_col = $('<div/>').addClass('engines_col col-xs-3').text(this.data.n);
        var stop_button = $('<button/>').addClass("btn btn-default btn-xs").text("Stop");
        var action_col = $('<div/>').addClass('action_col col-xs-2').append(
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
                error : function (xhr, status, error) {
                    utils.log_ajax_error(xhr, status, error),
                    status_col.text("error stopping cluster");
                }
            };
            status_col.text('stopping');
            var url = utils.url_join_encode(
                that.base_url,
                'clusters',
                that.data.profile,
                'stop'
            );
            $.ajax(url, settings);
        });
    };

    // For backwards compatability.
    IPython.ClusterList = ClusterList;
    IPython.ClusterItem = ClusterItem;

    return {
        'ClusterList': ClusterList,
        'ClusterItem': ClusterItem,
    };
});
