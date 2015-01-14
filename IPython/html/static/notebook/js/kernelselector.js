// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";
    
    var KernelSelector = function(selector, notebook) {
        var that = this;
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
        this._finish_load = null;
        this.loaded = new Promise(function(resolve, reject) {
            that._finish_load = resolve;
        });
        
        Object.seal(this);
    };
    
    KernelSelector.prototype.request_kernelspecs = function() {
        var url = utils.url_join_encode(this.notebook.base_url, 'api/kernelspecs');
        utils.promising_ajax(url).then($.proxy(this._got_kernelspecs, this));
    };
    
    KernelSelector.prototype._got_kernelspecs = function(data) {
        this.kernelspecs = data.kernelspecs;
        var change_kernel_submenu = $("#menu-change-kernel-submenu");
        var new_notebook_submenu = $("#menu-new-notebook-submenu");
        
        var keys = Object.keys(data.kernelspecs).sort(function (a, b) {
            // sort by display_name
            var da = data.kernelspecs[a].spec.display_name;
            var db = data.kernelspecs[b].spec.display_name;
            if (da === db) {
                return 0;
            } else if (da > db) {
                return 1;
            } else {
                return -1;
            }
        });
        
        var i, ks, ks_submenu_entry;
        // Create the Kernel > Change kernel submenu
        for (i = 0; i < keys.length; i++) {
            ks = this.kernelspecs[keys[i]];
            ks_submenu_entry = $("<li>").attr("id", "kernel-submenu-"+ks.name).append($('<a>')
                .attr('href', '#')
                .click(function(){
                        $.proxy(this.set_kernel, this, ks.name)
                        event.preventDefault();
                    })
                .text(ks.spec.display_name));
            change_kernel_submenu.append(ks_submenu_entry);
        }
        
        // Create the File > New Notebook submenu
        for (i = 0; i < keys.length; i++) {
            ks = this.kernelspecs[keys[i]];
            ks_submenu_entry = $("<li>").attr("id", "new-notebook-submenu-"+ks.name).append($('<a>')
                .attr('href', '#')
                .click(function(){
                        $.proxy(this.new_notebook, this, ks.name)
                        event.preventDefault();
                    })
                .text(ks.spec.display_name));
            new_notebook_submenu.append(ks_submenu_entry);
        }
        // trigger loaded promise
        this._finish_load();
    };
    
    KernelSelector.prototype._spec_changed = function (event, ks) {
        /** event handler for spec_changed */
        
        // update selection
        this.current_selection = ks.name;
        
        // put the current kernel at the top of File > New Notebook
        var cur_kernel_entry = $("#new-notebook-submenu-" + ks.name);
        var parent = cur_kernel_entry.parent();
        // do something only if there is more than one kernel
        if (parent.children().length > 1) {
            // first, sort back the submenu
            parent.append(
                parent.children("li[class!='divider']").sort(
                    function (a,b) {
                        var da = $("a",a).text();
                        var db = $("a",b).text();
                        if (da === db) {
                            return 0;
                        } else if (da > db) {
                            return 1;
                        } else {
                            return -1;
                        }}));
            // then, if there is no divider yet, add one
            if (!parent.children("li[class='divider']").length) {
                parent.prepend($("<li>").attr("class","divider"));
            } 
            // finally, put the current kernel at the top
            parent.prepend(cur_kernel_entry);
        }
        
        // load logo
        var logo_img = this.element.find("img.current_kernel_logo");
        $("#kernel_indicator").find('.kernel_indicator_name').text(ks.spec.display_name);
        if (ks.resources['logo-64x64']) {
            logo_img.attr("src", ks.resources['logo-64x64']);
            logo_img.show();
        } else {
            logo_img.hide();
        }
        
        // load kernel css
        var css_url = ks.resources['kernel.css'];
        if (css_url) {
            $('#kernel-css').attr('href', css_url);
        } else {
            $('#kernel-css').attr('href', '');
        }
        
        // load kernel js
        if (ks.resources['kernel.js']) {
            require([ks.resources['kernel.js']],
                function (kernel_mod) {
                    if (kernel_mod && kernel_mod.onload) {
                        kernel_mod.onload();
                    } else {
                        console.warn("Kernel " + ks.name + " has a kernel.js file that does not contain "+
                                     "any asynchronous module definition. This is undefined behavior "+
                                     "and not recommended.");
                    }
                }, function (err) {
                    console.warn("Failed to load kernel.js from ", ks.resources['kernel.js'], err);
                }
            );
        }
    };

    KernelSelector.prototype.set_kernel = function (kernel_name) {
        /** set the kernel by name, ensuring kernelspecs have been loaded, first */
        var that = this;
        return this.loaded.then(function () {
            that._set_kernel(kernel_name);
        });
    };

    KernelSelector.prototype._set_kernel = function (kernel_name) {
        /** Actually set the kernel (kernelspecs have been loaded) */
        if (kernel_name === this.current_selection) {
            // only trigger event if value changed
            return;
        }
        var ks = this.kernelspecs[kernel_name];
        if (this.notebook._session_starting) {
            console.error("Cannot change kernel while waiting for pending session start.");
            return;
        }
        this.current_selection = kernel_name;
        this.events.trigger('spec_changed.Kernel', ks);
    };

    KernelSelector.prototype.new_notebook = function (kernel_name) {
        
        var w = window.open();
        // Create a new notebook in the same path as the current
        // notebook's path.
        var that = this;
        var parent = utils.url_path_split(that.notebook.notebook_path)[0];
        that.notebook.contents.new_untitled(parent, {type: "notebook"}).then(
            function (data) {
                var url = utils.url_join_encode(
                    that.notebook.base_url, 'notebooks', data.path
                );
                url += "?kernel_name=" + kernel_name;
                w.location = url;
            },
            function(error) {
                w.close();
                dialog.modal({
                    title : 'Creating Notebook Failed',
                    body : "The error was: " + error.message,
                    buttons : {'OK' : {'class' : 'btn-primary'}}
                });
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
        this.events.on('spec_changed.Kernel', $.proxy(this._spec_changed, this));

        this.events.on('kernel_created.Session', function (event, data) {
            that.set_kernel(data.kernel.name);
        });
        
        var logo_img = this.element.find("img.current_kernel_logo");
        logo_img.on("load", function() {
            logo_img.show();
        });
        logo_img.on("error", function() {
            logo_img.hide();
        });
    };

    return {'KernelSelector': KernelSelector};
});
