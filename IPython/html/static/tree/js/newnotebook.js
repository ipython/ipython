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
        this.kernelspecs = {};
        var menu = this.element.find("#new-notebook-menu");
        for (var i = 0; i < data.length; i++) {
            var ks = data[i];
            this.kernelspecs[ks.name] = ks;
            var li = $("<li>")
                .attr("id", "kernel-" +ks.name)
                .data('kernelspec', ks).append(
                    $('<a>').attr('href', '#').append($('<i>')
                        .addClass('kernel-menu-icon fa')
                        .attr('href', '#')
                        .click($.proxy(this.select_kernel, this, ks.name))
                    ).append($('<span>')
                        .attr('href', '#')
                        .click($.proxy(this.new_notebook, this, ks.name))
                        .text(ks.display_name)
                        .attr('title', 'Create a new notebook with ' + ks.display_name)
                    )
            );
            menu.append(li);
        }
        this._load_default_kernelspec();
    };
    
    NewNotebookWidget.prototype._load_default_kernelspec = function () {
        /** load default kernelspec name from localStorage, if defined */
        this.select_kernel(localStorage.default_kernel_name);
    };

    NewNotebookWidget.prototype.select_kernel = function (kernel_name) {
        /** select the current default kernel */
        this.current_selection = kernel_name;
        var spec = this.kernelspecs[kernel_name];
        var display_name;
        if (spec) {
            display_name = spec.display_name;
            localStorage.default_kernel_name = kernel_name;
            this.element.find("#current-kernel").text(display_name);
        } else {
            display_name = 'default kernel';
            delete localStorage.default_kernel_name;
        }
        this.element.find("#new_notebook").attr('title',
            'Create a new notebook with ' + display_name
        );
        this.element.find("li").map(function (i, li) {
            li = $(li);
            var ks = li.data('kernelspec');
            if (ks.name == kernel_name) {
                li.find(".kernel-menu-icon")
                    .attr('title', display_name + ' is the default kernel')
                    .addClass("kernel-menu-icon-current");
            } else {
                li.find(".kernel-menu-icon")
                    .attr('title', 'Make ' + ks.display_name + ' the default kernel')
                    .removeClass("kernel-menu-icon-current");
            }
        });
    };
    
    NewNotebookWidget.prototype.new_with_kernel = function (kernel_name) {
        /** record current selection and open a new notebook */
        this.new_notebook(kernel_name);
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
