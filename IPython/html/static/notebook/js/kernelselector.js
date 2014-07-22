// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";
    
    var KernelSelector = function(selector, notebook) {
        this.selector = selector;
        this.notebook = notebook;
        this.events = notebook.events;
        this.kernelspecs = {};
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.request_kernelspecs();
        }
        this.bind_events();
        // For now, this is how we make this object available elsewhere
        IPython.kernelselector = this;
    };
    
    KernelSelector.prototype.request_kernelspecs = function() {
        var url = utils.url_join_encode(this.notebook.base_url, 'api/kernelspecs');
        $.ajax(url, {success: $.proxy(this.got_kernelspecs, this)});
    };
    
    KernelSelector.prototype.got_kernelspecs = function(data, status, xhr) {
        this.kernelspecs = {};
        var menu = this.element.find("#kernel_selector");
        for (var i = 0; i < data.length; i++) {
            var ks = data[i];
            this.kernelspecs[ks.name] = ks;
            var ksentry = $("<li>").attr("id", "kernel-" +ks.name).append($('<a>')
                .attr('href', '#')
                .click($.proxy(this.change_kernel, this, ks.name))
                .text(ks.display_name));
            menu.append(ksentry);
        }
    };

    KernelSelector.prototype.change_kernel = function(kernel_name) {
        if (kernel_name === this.notebook.kernel.name) {
            return;
        }
        var ks = this.kernelspecs[kernel_name];
        this.events.trigger('spec_changed.Kernel', ks);
        this.notebook.session.delete();
        this.notebook.start_session(kernel_name);
    };
    
    KernelSelector.prototype.bind_events = function() {
        var that = this;
        this.events.on('spec_changed.Kernel', function(event, data) {
            that.element.find("#current_kernel_spec").find('.kernel_name').text(data.display_name);
        });
    };

    return {'KernelSelector': KernelSelector};
});
