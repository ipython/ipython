// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'base/js/utils',
    'jquery',
    'tree/js/notebooklist',
], function(IPython, utils, $, notebooklist) {
    "use strict";

    var TerminalList = function (selector, options) {
        // Constructor
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          base_url: string
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.element_name = options.element_name || 'terminal';
        this.selector = selector;
        this.terminals = [];
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
            this.load_terminals();
        }
    };

    TerminalList.prototype = Object.create(notebooklist.NotebookList.prototype);

    TerminalList.prototype.bind_events = function () {
        var that = this;
        $('#refresh_' + this.element_name + '_list').click(function () {
            that.load_terminals();
        });
        $('#new_terminal').click($.proxy(this.new_terminal, this));
    };

    TerminalList.prototype.new_terminal = function () {
        var settings = {
            type : "POST",
            cache : false,
            async : false,
            success : function (data, status, xhr) {
                var name = data.name;
                window.open(
                    utils.url_join_encode(
                        this.base_url,
                        'terminals',
                        name),
                    '_blank'
                );
            },
            error : utils.log_ajax_error,
        };
        var url = utils.url_join_encode(
            this.base_url,
            'api/terminals'
        );
        $.ajax(url, settings);
    };
    
    TerminalList.prototype.load_terminals = function() {
        var that = this;
        var url = utils.url_join_encode(this.base_url, 'api/terminals');
        $.ajax(url, {
            type: "GET",
            cache: false,
            dataType: "json",
            success: $.proxy(this.terminals_loaded, this),
            error : utils.log_ajax_error
        });
    };

    TerminalList.prototype.terminals_loaded = function (data) {
        this.terminals = data;
        this.clear_list();
        var item, path_name, term;
        for (var i=0; i < this.terminals.length; i++) {
            term = this.terminals[i];
            item = this.new_item(-1);
            this.add_link(term.name, item);
            this.add_shutdown_button(term.name, item);
        }
        $('#terminal_list_header').toggle(data.length === 0);
    };
    
    TerminalList.prototype.add_link = function(name, item) {
        item.data('term-name', name);
        item.find(".item_name").text("terminals/" + name);
        item.find(".item_icon").addClass("fa fa-terminal");
        var link = item.find("a.item_link")
            .attr('href', utils.url_join_encode(this.base_url, "terminals", name));
        link.attr('target', '_blank');
        this.add_shutdown_button(name, item);
    };
    
    TerminalList.prototype.add_shutdown_button = function(name, item) {
        var that = this;
        var shutdown_button = $("<button/>").text("Shutdown").addClass("btn btn-xs btn-danger").
            click(function (e) {
                var settings = {
                    processData : false,
                    type : "DELETE",
                    dataType : "json",
                    success : function () {
                        that.load_terminals();
                    },
                    error : utils.log_ajax_error,
                };
                var url = utils.url_join_encode(that.base_url, 'api/terminals', name);
                $.ajax(url, settings);
                return false;
            });
        item.find(".item_buttons").text("").append(shutdown_button);
    };

    return {TerminalList: TerminalList};
});
