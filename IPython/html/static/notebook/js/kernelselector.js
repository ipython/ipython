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
        Object.seal(this);
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
        /**
         * TODO, have a methods to set kernel spec directly ?
         **/
        var that = this;
        if (kernel_name === this.current_selection) {
            return;
        }
        var ks = this.kernelspecs[kernel_name];
        var new_mod = 'kernelspecs/'+ks.name+'/custom';
        var old_mod;
        if(this.current_selection){
            old_mod = 'kernelspecs/'+this.current_selection+'/custom';
        }

        var css_url = this.notebook.base_url+new_mod+'.css';
        console.warn();
        $.ajax({
            type: 'HEAD',
            url: css_url,
            success: function(){
                $('#kernel-css')
                .attr('href',css_url);
            },
            error:function(){
                console.warn('Having a 404 on the following url is normal:',css_url );
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

        // we need a handle on both the old and new kernel 
        // the old one might want to undo some things
        // set up the callback that will be trigger once 
        // the new mode is loaded, ie patch. 
        var require_new_mode_and_patch = function(){
            require([new_mod], 
                // if new mode has custom.js
                function(new_mode){
                    if(new_mode.patch){new_mode.patch();}
                }, function(err){
                    // if new mode does not have custom.js
                    console.warn('Any above 404 on ',new_mod+'.js is normal');
                }
        );};

        // finally require the 'old/current' mode, 
        // - call its unpatch method if it exist.
        // - after call newmode.patch
        if(!old_mod){
            require_new_mode_and_patch();
        } else {
            require([old_mod], 
                    function(old_mode){
                        console.warn(old_mod, new_mod);
                        if(old_mode.unpatch){ old_mode.unpatch();}
                        require_new_mode_and_patch();
                    }, function(err){
                        require_new_mode_and_patch();
                    }

             );
        }
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
