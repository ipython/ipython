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
        this.kernelspecs = {};
        this.current = "python";
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.request_kernelspecs();
        }
    };
    
    KernelSelector.prototype.style = function() {
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
        console.log("change_kernel " + kernel_name + " from " + this.current);
        if (kernel_name === this.current) {
            return;
        }
        this.notebook.session.delete();
        this.notebook.start_session(kernel_name);
        this.current = kernel_name;
        var display_name = this.kernelspecs[kernel_name].display_name;
        this.element.find("#current_kernel_spec").text(display_name);
    };
    
    return {'KernelSelector': KernelSelector};
});
