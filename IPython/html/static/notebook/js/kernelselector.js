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
        this.current_selection = null;
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
        utils.promising_ajax(url).then($.proxy(this._got_kernelspecs, this));
    };
    
    KernelSelector.prototype._got_kernelspecs = function(data) {
        this.kernelspecs = data.kernelspecs;
        var menu = this.element.find("#kernel_selector");
        var change_kernel_submenu = $("#menu-change-kernel-submenu");
        var keys = Object.keys(data.kernelspecs).sort(function (a, b) {
            // sort by display_name
            var da = data.kernelspecs[a].display_name;
            var db = data.kernelspecs[b].display_name;
            if (da === db) {
                return 0;
            } else if (da > db) {
                return 1;
            } else {
                return -1;
            }
        });
        for (var i = 0; i < keys.length; i++) {
            var ks = this.kernelspecs[keys[i]];
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
        try {
            this.notebook.start_session(kernel_name);
        } catch (e) {
            if (e.name === 'SessionAlreadyStarting') {
                console.log("Cannot change kernel while waiting for pending session start.");
            } else {
                // unhandled error
                throw e;
            }
            // only trigger spec_changed if change was successful
            return;
        }
        this.events.trigger('spec_changed.Kernel', ks);
    };
    
    KernelSelector.prototype.bind_events = function() {
        var that = this;
        this.events.on('spec_changed.Kernel', function(event, data) {
            that.current_selection = data.name;
            that.element.find("#current_kernel_spec").find('.kernel_name').text(data.display_name);
            that.element.find("#current_kernel_logo").attr("src", "/kernelspecs/"+data.name+"/logo-32.png");
        });
        
        this.events.on('kernel_created.Session', function(event, data) {
            if (data.kernel.name !== that.current_selection) {
                // If we created a 'python' session, we only know if it's Python
                // 3 or 2 on the server's reply, so we fire the event again to
                // set things up.
                var ks = that.kernelspecs[data.kernel.name];
                that.events.trigger('spec_changed.Kernel', ks);
            }
        });
        
        var logo_img = this.element.find("#current_kernel_logo")
        logo_img.on("load", function() {
            logo_img.show();
        });
        logo_img.on("error", function() {
            logo_img.hide();
        });
    };

    return {'KernelSelector': KernelSelector};
});
