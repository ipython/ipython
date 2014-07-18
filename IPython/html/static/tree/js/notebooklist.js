// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'base/js/dialog',
], function(IPython, $, utils, dialog) {
    "use strict";
    
    var NotebookList = function (selector, options) {
        // Constructor
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          session_list: SessionList instance
        //          element_name: string
        //          base_url: string
        //          notebook_path: string
        var that = this;
        this.session_list = options.session_list;
        // allow code re-use by just changing element_name in kernellist.js
        this.element_name = options.element_name || 'notebook';
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
            this.bind_events();
        }
        this.notebooks_list = [];
        this.sessions = {};
        this.base_url = options.base_url || utils.get_body_data("baseUrl");
        this.notebook_path = options.notebook_path || utils.get_body_data("notebookPath");
        if (this.session_list && this.session_list.events) {
            this.session_list.events.on('sessions_loaded.Dashboard', 
                function(e, d) { that.sessions_loaded(d); });
        }
    };

    NotebookList.prototype.style = function () {
        var prefix = '#' + this.element_name;
        $(prefix + '_toolbar').addClass('list_toolbar');
        $(prefix + '_list_info').addClass('toolbar_info');
        $(prefix + '_buttons').addClass('toolbar_buttons');
        $(prefix + '_list_header').addClass('list_header');
        this.element.addClass("list_container");
    };


    NotebookList.prototype.bind_events = function () {
        var that = this;
        $('#refresh_' + this.element_name + '_list').click(function () {
            that.load_sessions();
        });
        this.element.bind('dragover', function () {
            return false;
        });
        this.element.bind('drop', function(event){
            that.handleFilesUpload(event,'drop');
            return false;
        });
    };

    NotebookList.prototype.handleFilesUpload =  function(event, dropOrForm) {
        var that = this;
        var files;
        if(dropOrForm =='drop'){
            files = event.originalEvent.dataTransfer.files;
        } else 
        {
            files = event.originalEvent.target.files;
        }
        for (var i = 0; i < files.length; i++) {
            var f = files[i];
            var reader = new FileReader();
            reader.readAsText(f);
            var name_and_ext = utils.splitext(f.name);
            var file_ext = name_and_ext[1];
            if (file_ext === '.ipynb') {
                var item = that.new_notebook_item(0);
                item.addClass('new-file');
                that.add_name_input(f.name, item);
                // Store the notebook item in the reader so we can use it later
                // to know which item it belongs to.
                $(reader).data('item', item);
                reader.onload = function (event) {
                    var nbitem = $(event.target).data('item');
                    that.add_notebook_data(event.target.result, nbitem);
                    that.add_upload_button(nbitem);
                };
            } else {
                var dialog_body = 'Uploaded notebooks must be .ipynb files';
                dialog.modal({
                    title : 'Invalid file type',
                    body : dialog_body,
                    buttons : {'OK' : {'class' : 'btn-primary'}}
                });
            }
        }
        // Replace the file input form wth a clone of itself. This is required to
        // reset the form. Otherwise, if you upload a file, delete it and try to 
        // upload it again, the changed event won't fire.
        var form = $('input.fileinput');
        form.replaceWith(form.clone(true));
        return false;
    };

    NotebookList.prototype.clear_list = function (remove_uploads) {
        // Clears the navigation tree.
        //
        // Parameters
        // remove_uploads: bool=False
        //      Should upload prompts also be removed from the tree.
        if (remove_uploads) {
            this.element.children('.list_item').remove();
        } else {
            this.element.children('.list_item:not(.new-file)').remove();  
        }
    };

    NotebookList.prototype.load_sessions = function(){
        this.session_list.load_sessions();
    };


    NotebookList.prototype.sessions_loaded = function(data){
        this.sessions = data;
        this.load_list();
    };

    NotebookList.prototype.load_list = function () {
        var that = this;
        var settings = {
            processData : false,
            cache : false,
            type : "GET",
            dataType : "json",
            success : $.proxy(this.list_loaded, this),
            error : $.proxy( function(xhr, status, error){
                utils.log_ajax_error(xhr, status, error);
                that.list_loaded([], null, null, {msg:"Error connecting to server."});
                             },this)
        };

        var url = utils.url_join_encode(
                this.base_url,
                'api',
                'notebooks',
                this.notebook_path
        );
        $.ajax(url, settings);
    };


    NotebookList.prototype.list_loaded = function (data, status, xhr, param) {
        var message = 'Notebook list empty.';
        if (param !== undefined && param.msg) {
            message = param.msg;
        }
        var item = null;
        var len = data.length;
        this.clear_list();
        if (len === 0) {
            item = this.new_notebook_item(0);
            var span12 = item.children().first();
            span12.empty();
            span12.append($('<div style="margin:auto;text-align:center;color:grey"/>').text(message));
        }
        var path = this.notebook_path;
        var offset = 0;
        if (path !== '') {
            item = this.new_notebook_item(0);
            this.add_dir(path, '..', item);
            offset = 1;
        }
        for (var i=0; i<len; i++) {
            if (data[i].type === 'directory') {
                var name = data[i].name;
                item = this.new_notebook_item(i+offset);
                this.add_dir(path, name, item);
            } else {
                var name = data[i].name;
                item = this.new_notebook_item(i+offset);
                this.add_link(path, name, item);
                name = utils.url_path_join(path, name);
                if(this.sessions[name] === undefined){
                    this.add_delete_button(item);
                } else {
                    this.add_shutdown_button(item,this.sessions[name]);
                }
            }
        }
    };


    NotebookList.prototype.new_notebook_item = function (index) {
        var item = $('<div/>').addClass("list_item").addClass("row");
        // item.addClass('list_item ui-widget ui-widget-content ui-helper-clearfix');
        // item.css('border-top-style','none');
        item.append($("<div/>").addClass("col-md-12").append(
            $('<i/>').addClass('item_icon')
        ).append(
            $("<a/>").addClass("item_link").append(
                $("<span/>").addClass("item_name")
            )
        ).append(
            $('<div/>').addClass("item_buttons btn-group pull-right")
        ));
        
        if (index === -1) {
            this.element.append(item);
        } else {
            this.element.children().eq(index).after(item);
        }
        return item;
    };


    NotebookList.prototype.add_dir = function (path, name, item) {
        item.data('name', name);
        item.data('path', path);
        item.find(".item_name").text(name);
        item.find(".item_icon").addClass('folder_icon').addClass('icon-fixed-width');
        item.find("a.item_link")
            .attr('href',
                utils.url_join_encode(
                    this.base_url,
                    "tree",
                    path,
                    name
                )
            );
    };


    NotebookList.prototype.add_link = function (path, nbname, item) {
        item.data('nbname', nbname);
        item.data('path', path);
        item.find(".item_name").text(nbname);
        item.find(".item_icon").addClass('notebook_icon').addClass('icon-fixed-width');
        item.find("a.item_link")
            .attr('href',
                utils.url_join_encode(
                    this.base_url,
                    "notebooks",
                    path,
                    nbname
                )
            ).attr('target','_blank');
    };


    NotebookList.prototype.add_name_input = function (nbname, item) {
        item.data('nbname', nbname);
        item.find(".item_icon").addClass('notebook_icon').addClass('icon-fixed-width');
        item.find(".item_name").empty().append(
            $('<input/>')
            .addClass("nbname_input")
            .attr('value', utils.splitext(nbname)[0])
            .attr('size', '30')
            .attr('type', 'text')
        );
    };


    NotebookList.prototype.add_notebook_data = function (data, item) {
        item.data('nbdata', data);
    };


    NotebookList.prototype.add_shutdown_button = function (item, session) {
        var that = this;
        var shutdown_button = $("<button/>").text("Shutdown").addClass("btn btn-xs btn-danger").
            click(function (e) {
                var settings = {
                    processData : false,
                    cache : false,
                    type : "DELETE",
                    dataType : "json",
                    success : function () {
                        that.load_sessions();
                    },
                    error : utils.log_ajax_error,
                };
                var url = utils.url_join_encode(
                    that.base_url,
                    'api/sessions',
                    session
                );
                $.ajax(url, settings);
                return false;
            });
        // var new_buttons = item.find('a'); // shutdown_button;
        item.find(".item_buttons").text("").append(shutdown_button);
    };

    NotebookList.prototype.add_delete_button = function (item) {
        var new_buttons = $('<span/>').addClass("btn-group pull-right");
        var notebooklist = this;
        var delete_button = $("<button/>").text("Delete").addClass("btn btn-default btn-xs").
            click(function (e) {
                // $(this) is the button that was clicked.
                var that = $(this);
                // We use the nbname and notebook_id from the parent notebook_item element's
                // data because the outer scopes values change as we iterate through the loop.
                var parent_item = that.parents('div.list_item');
                var nbname = parent_item.data('nbname');
                var message = 'Are you sure you want to permanently delete the notebook: ' + nbname + '?';
                dialog.modal({
                    title : "Delete notebook",
                    body : message,
                    buttons : {
                        Delete : {
                            class: "btn-danger",
                            click: function() {
                                var settings = {
                                    processData : false,
                                    cache : false,
                                    type : "DELETE",
                                    dataType : "json",
                                    success : function (data, status, xhr) {
                                        parent_item.remove();
                                    },
                                    error : utils.log_ajax_error,
                                };
                                var url = utils.url_join_encode(
                                    notebooklist.base_url,
                                    'api/notebooks',
                                    notebooklist.notebook_path,
                                    nbname
                                );
                                $.ajax(url, settings);
                            }
                        },
                        Cancel : {}
                    }
                });
                return false;
            });
        item.find(".item_buttons").text("").append(delete_button);
    };


    NotebookList.prototype.add_upload_button = function (item) {
        var that = this;
        var upload_button = $('<button/>').text("Upload")
            .addClass('btn btn-primary btn-xs upload_button')
            .click(function (e) {
                var nbname = item.find('.item_name > input').val();
                if (nbname.slice(nbname.length-6, nbname.length) != ".ipynb") {
                    nbname = nbname + ".ipynb";
                }
                var path = that.notebook_path;
                var nbdata = item.data('nbdata');
                var content_type = 'application/json';
                var model = {
                    content : JSON.parse(nbdata),
                };
                var settings = {
                    processData : false,
                    cache : false,
                    type : 'PUT',
                    dataType : 'json',
                    data : JSON.stringify(model),
                    headers : {'Content-Type': content_type},
                    success : function (data, status, xhr) {
                        that.add_link(path, nbname, item);
                        that.add_delete_button(item);
                    },
                    error : utils.log_ajax_error,
                };

                var url = utils.url_join_encode(
                    that.base_url,
                    'api/notebooks',
                    that.notebook_path,
                    nbname
                );
                $.ajax(url, settings);
                return false;
            });
        var cancel_button = $('<button/>').text("Cancel")
            .addClass("btn btn-default btn-xs")
            .click(function (e) {
                console.log('cancel click');
                item.remove();
                return false;
            });
        item.find(".item_buttons").empty()
            .append(upload_button)
            .append(cancel_button);
    };


    NotebookList.prototype.new_notebook = function(){
        var path = this.notebook_path;
        var base_url = this.base_url;
        var settings = {
            processData : false,
            cache : false,
            type : "POST",
            dataType : "json",
            async : false,
            success : function (data, status, xhr) {
                var notebook_name = data.name;
                window.open(
                    utils.url_join_encode(
                        base_url,
                        'notebooks',
                        path,
                        notebook_name),
                    '_blank'
                );
            },
            error : $.proxy(this.new_notebook_failed, this),
        };
        var url = utils.url_join_encode(
            base_url,
            'api/notebooks',
            path
        );
        $.ajax(url, settings);
    };
    
    
    NotebookList.prototype.new_notebook_failed = function (xhr, status, error) {
        utils.log_ajax_error(xhr, status, error);
        var msg;
        if (xhr.responseJSON && xhr.responseJSON.message) {
            msg = xhr.responseJSON.message;
        } else {
            msg = xhr.statusText;
        }
        dialog.modal({
            title : 'Creating Notebook Failed',
            body : "The error was: " + msg,
            buttons : {'OK' : {'class' : 'btn-primary'}}
        });
    };
    
    // Backwards compatability.    
    IPython.NotebookList = NotebookList;

    return {'NotebookList': NotebookList};
});
