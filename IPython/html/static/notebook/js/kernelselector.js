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
        this.current_selection = notebook.default_kernel_name;
        this.kernelspecs = {};
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.request_kernelspecs();
        }
        this.bind_events();
        // Make the object globally available for user convenience & inspection
        IPython.kernelselector = this;
    };
    
    KernelSelector.prototype.request_kernelspecs = function() {
        var url = utils.url_join_encode(this.notebook.base_url, 'api/kernelspecs');
        $.ajax(url, {success: $.proxy(this._got_kernelspecs, this)});
    };
    
    KernelSelector.prototype._got_kernelspecs = function(data, status, xhr) {
        this.kernelspecs = {};
        var menu = this.element.find("#kernel_selector");
        var change_kernel_submenu = $("#menu-change-kernel-submenu");
        for (var i = 0; i < data.length; i++) {
            var ks = data[i];
            this.kernelspecs[ks.name] = ks;
            var ksentry = $("<li>").attr("id", "kernel-" +ks.name).append($('<a>')
                .attr('href', '#')
                .click($.proxy(this.change_kernel, this, ks.name))
                .text(ks.display_name));
            menu.append(ksentry);

            var ks_submenu_entry = $("<li>").attr("id", "kernel-submenu-"+ks.name).append($('<a>')
                .attr('href', '#')
                .click($.proxy(this.change_kernel, this, ks.name))
                .text(ks.display_name));
            change_kernel_submenu.append(ks_submenu_entry);
        }
    };

    KernelSelector.prototype.change_kernel = function(kernel_name) {
        if (kernel_name === this.current_selection) {
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
            that.current_selection = data.name;
            that.element.find("#current_kernel_spec").find('.kernel_name').text(data.display_name);
        });
        
        this.events.on('started.Session', function(events, session) {
            if (session.kernel_name !== that.current_selection) {
                // If we created a 'python' session, we only know if it's Python
                // 3 or 2 on the server's reply, so we fire the event again to
                // set things up.
                var ks = that.kernelspecs[session.kernel_name];
                that.events.trigger('spec_changed.Kernel', ks);
            }
        });
    };

    return {'KernelSelector': KernelSelector};
});
