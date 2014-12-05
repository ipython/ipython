// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/namespace',
    'base/js/utils',
    'base/js/dialog',
], function ($, IPython, utils, dialog) {
    "use strict";
    
    var NewNotebookWidget = function (selector, options) {
        this.selector = selector;
        this.base_url = options.base_url;
        this.notebook_path = options.notebook_path;
        this.contents = options.contents;
        this.current_selection = null;
        this.config = options.config;
        this.kernelspecs = {};
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.request_kernelspecs();
        }
        this.bind_events();
    };
    
    NewNotebookWidget.prototype.bind_events = function () {
        var that = this;
        this.element.find('#new_notebook').click(function () {
            that.new_notebook();
        });
    };
    
    NewNotebookWidget.prototype.request_kernelspecs = function () {
        /** request and then load kernel specs */
        var url = utils.url_join_encode(this.base_url, 'api/kernelspecs');
        utils.promising_ajax(url).then($.proxy(this._load_kernelspecs, this));
    };
    
    NewNotebookWidget.prototype._load_kernelspecs = function (data) {
        /** load kernelspec list */
        var that = this;
        this.kernelspecs = data.kernelspecs;
        var menu = this.element.find("#new-notebook-menu");
        var keys = Object.keys(data.kernelspecs).sort(function (a, b) {
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
            var li = $("<li>")
                .attr("id", "kernel-" +ks.name)
                .data('kernelspec', ks).append(
                    $('<a>')
                        .attr('href', '#')
                        .click($.proxy(this.new_notebook, this, ks.name))
                        .text(ks.display_name)
                        .attr('title', 'Create a new notebook with ' + ks.display_name)
                );
            menu.append(li);
        }
        this.config.loaded.then(function () {
            that._load_default_kernelspec(data['default']);
        });
    };
    
    NewNotebookWidget.prototype._load_default_kernelspec = function (default_name) {
        /** load default kernelspec name from config, if defined */
        if (this.config.data.NewNotebookWidget &&
            this.config.data.NewNotebookWidget.current_selection &&
            this.kernelspecs[this.config.data.NewNotebookWidget.current_selection] !== undefined
        ) {
            default_name = this.config.data.NewNotebookWidget.current_selection;
        }
        this.set_default_kernel(default_name);
    };

    NewNotebookWidget.prototype.set_default_kernel = function (kernel_name) {
        /** select the current default kernel */
        this.current_selection = kernel_name;
        this.config.update({
            NewNotebookWidget: {
                current_selection: kernel_name
            }
        });
        var spec = this.kernelspecs[kernel_name];
        var display_name;
        if (spec) {
            display_name = spec.display_name;
            this.element.find("#current-kernel")
                .text(display_name)
                .attr('title', display_name + " is the default kernel for new notebooks");
        } else {
            display_name = 'default kernel';
        }
        this.element.find("#new_notebook").attr('title',
            'Create a new notebook with ' + display_name
        );
    };
    
    NewNotebookWidget.prototype.new_notebook = function (kernel_name) {
        /** create and open a new notebook */
        var that = this;
        kernel_name = kernel_name || this.current_selection;
        var w = window.open();
        this.contents.new_untitled(that.notebook_path, {type: "notebook"}).then(
            function (data) {
                var url = utils.url_join_encode(
                    that.base_url, 'notebooks', data.path
                );
                if (kernel_name) {
                    url += "?kernel_name=" + kernel_name;
                }
                w.location = url;
            },
            function (error) {
                w.close();
                dialog.modal({
                    title : 'Creating Notebook Failed',
                    body : "The error was: " + error.message,
                    buttons : {'OK' : {'class' : 'btn-primary'}}
                });
            }
        );
    };
    
    return {'NewNotebookWidget': NewNotebookWidget};
});
