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
        this.notebook.set_kernelselector(this);
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
        Object.seal(this);
    };
    
    KernelSelector.prototype.request_kernelspecs = function() {
        var url = utils.url_join_encode(this.notebook.base_url, 'api/kernelspecs');
        utils.promising_ajax(url).then($.proxy(this._got_kernelspecs, this));
    };
    
    KernelSelector.prototype._got_kernelspecs = function(data) {
        this.kernelspecs = data.kernelspecs;
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
            var ks_submenu_entry = $("<li>").attr("id", "kernel-submenu-"+ks.name).append($('<a>')
                .attr('href', '#')
                .click($.proxy(this.change_kernel, this, ks.name))
                .text(ks.display_name));
            change_kernel_submenu.append(ks_submenu_entry);
        }
    };

    KernelSelector.prototype.change_kernel = function(kernel_name) {
        /**
         * TODO, have a methods to set kernel spec directly ?
         **/
        var that = this;
        if (kernel_name === this.current_selection) {
            return;
        }
        var ks = this.kernelspecs[kernel_name];
        var new_mode_url = 'kernelspecs/'+ks.name+'/kernel';

        var css_url = this.notebook.base_url+new_mode_url+'.css';
        $.ajax({
            type: 'HEAD',
            url: css_url,
            success: function(){
                $('#kernel-css')
                .attr('href',css_url);
            },
            error:function(){
                console.info("No custom kernel.css at URL:", css_url)
            }
        });

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


        // load new mode kernel.js if exist
        require([new_mode_url],
            // if new mode has custom.js
            function(new_mode){
                that.lock_switch();
                if(new_mode && new_mode.onload){
                    new_mode.onload();
                } else {
                    console.warn("The current kernel defined a kernel.js file but does not contain "+
                                 "any asynchronous module definition. This is undefined behavior "+
                                 "which is not recommended");
                }
            },
            function(err){
                // if new mode does not have custom.js
                console.info("No custom kernel.css at URL:", new_mode_url)
            }
        );
    };

    KernelSelector.prototype.lock_switch = function() {
        // should set a flag and display warning+reload if user want to
        // re-change kernel. As UI discussion never finish
        // making that a separate PR.
        console.warn('switching kernel is not guaranteed to work !');
    };

    KernelSelector.prototype.bind_events = function() {
        var that = this;
        this.events.on('spec_changed.Kernel', function(event, data) {
            that.current_selection = data.name;
            $("#kernel_indicator").find('.kernel_indicator_name').text(data.display_name);
            that.element.find("#current_kernel_logo").attr("src", that.notebook.base_url+"kernelspecs/"+data.name+"/logo-64x64.png");
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
        
        var logo_img = this.element.find("#current_kernel_logo");
        logo_img.on("load", function() {
            logo_img.show();
        });
        logo_img.on("error", function() {
            logo_img.hide();
        });
    };

    return {'KernelSelector': KernelSelector};
});
