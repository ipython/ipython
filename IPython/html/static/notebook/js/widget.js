//----------------------------------------------------------------------------
//  Copyright (C) 2013  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// WidgetModel, WidgetView, and WidgetManager
//============================================================================
/**
 * Base Widget classes
 * @module IPython
 * @namespace IPython
 * @submodule widget
 */

"use strict";

// Use require.js 'define' method so that require.js is intelligent enough to
// syncronously load everything within this file when it is being 'required' 
// elsewhere.
define(["static/components/underscore/underscore-min.js",
         "static/components/backbone/backbone-min.js",
        ], function(){

    // Only run once on a notebook.
    if (IPython.notebook.widget_manager == undefined) {

        //--------------------------------------------------------------------
        // WidgetModel class
        //--------------------------------------------------------------------
        var WidgetModel = Backbone.Model.extend({
            apply: function(sender) {
                this.save(this.changedAttributes(), {patch: true});

                for (var index in this.views) {
                    var view = this.views[index];
                    if (view !== sender) {
                        view.refresh();    
                    }
                }
            }
        });


        //--------------------------------------------------------------------
        // WidgetView class
        //--------------------------------------------------------------------
        var WidgetView = Backbone.View.extend({
            
            initialize: function() {
                this.model.on('change',this.refresh,this);
            },
            
            refresh: function() {
                this.update();
                
                if (this.model.css != undefined) {
                    for (var selector in this.model.css) {
                        if (this.model.css.hasOwnProperty(selector)) {
                            
                            // Get the elements via the css selector.  If the selector is
                            // blank, assume the current element is the target.
                            var elements = this.$el.find(selector);
                            if (selector=='') {
                                elements = this.$el;
                            }
                            
                            // Apply the css traits to all elements that match the selector.
                            if (elements.length>0){
                                var css_traits = this.model.css[selector];    
                                for (var css_key in css_traits) {
                                    if (css_traits.hasOwnProperty(css_key)) {
                                        elements.css(css_key, css_traits[css_key]);
                                    }
                                }
                            }
                        }
                    }
                }
            },
        });


        //--------------------------------------------------------------------
        // WidgetManager class
        //--------------------------------------------------------------------
        // Public constructor
        var WidgetManager = function(comm_manager){
            this.comm_manager = comm_manager;
            this.widget_model_types = {};
            this.widget_view_types = {};
            this.model_widget_views = {};
            this.pending_msgs = 0;
            this.msg_throttle = 3;
            this.msg_buffer = {};
            
            var that = this;
            Backbone.sync = function(method, model, options, error) {
                var result = that.handle_sync(method, model, options);
                if (options.success) {
                  options.success(result);
                }
            }; 
        }

        // Register a widget model type.
        WidgetManager.prototype.register_widget_model = function (widget_model_name, widget_model_type) {
            
            // Register the widget with the comm manager.  Make sure to pass this object's context
            // in so `this` works in the call back.
            this.comm_manager.register_target(widget_model_name, $.proxy(this.handle_com_open, this));
            
            // Register the types of the model and view correspong to this widget type.  Later
            // the widget manager will initialize these when the comm is opened.
            this.widget_model_types[widget_model_name] = widget_model_type;
        }

        // Register a widget view type.
        WidgetManager.prototype.register_widget_view = function (widget_view_name, widget_view_type) {
            this.widget_view_types[widget_view_name] = widget_view_type;
        }

        // Handle when a comm is opened.
        WidgetManager.prototype.handle_com_open = function (comm, msg) {
            var widget_type_name = msg.content.target_name;
            
            // Create the corresponding widget model.
            var widget_model = new this.widget_model_types[widget_type_name];

            // Remember comm associated with the model.
            widget_model.comm = comm;
            comm.model = widget_model;

            // Create an array to remember the views associated with the model.
            widget_model.views = [];

            // Add a handle to delete the control when the comm is closed.
            var that = this;
            var handle_close = function(msg) {
                that.handle_comm_closed(comm, msg);
            }
            comm.on_close(handle_close);

            // Handle incomming messages.
            var handle_msg = function(msg) {
                that.handle_comm_msg(comm, msg);
            }
            comm.on_msg(handle_msg);
        }

        // Create view that represents the model.
        WidgetManager.prototype.show_view = function (widget_area, widget_model, widget_view_name) {
            var widget_view = new this.widget_view_types[widget_view_name]({model: widget_model});
            widget_view.render();
            widget_model.views.push(widget_view);

            // Handle when the view element is remove from the page.
            widget_view.$el.on("remove", function(){ 
                var index = widget_model.views.indexOf(widget_view);
                if (index > -1) {
                    widget_model.views.splice(index, 1);
                }
                widget_view.remove(); // Clean-up view 

                // Close the comm if there are no views left.
                if (widget_model.views.length()==0) {
                    widget_model.comm.close();     
                }
            });

            // Add the view's element to cell's widget div.
            widget_area
                .append(widget_view.$el)
                .parent().show(); // Show the widget_area (parent of widget_subarea)

            // Update the view based on the model contents.
            widget_view.refresh();
        }

        // Handle incomming comm msg.
        WidgetManager.prototype.handle_comm_msg = function (comm, msg) {
            // Different logic for different methods.
            var method = msg.content.data.method;
            switch (method){
                case 'show':

                    // TODO: Get cell from registered output handler.
                    var cell = IPython.notebook.get_cell(IPython.notebook.get_selected_index()-1);
                    var widget_subarea = cell.element.find('.widget_area').find('.widget_subarea');

                    if (msg.content.data.parent != undefined) {
                        var find_results = widget_subarea.find("." + msg.content.data.parent);
                        if (find_results.length > 0) {
                            widget_subarea = find_results;
                        }
                    }

                    this.show_view(widget_subarea, comm.model, msg.content.data.view_name);
                    break;
                case 'update':
                    this.handle_update(comm, msg.content.data.state);
                    break;
            }
        }

        // Handle when a widget is updated via the python side.
        WidgetManager.prototype.handle_update = function (comm, state) {
            this.updating = true;
            for (var key in state) {
                if (state.hasOwnProperty(key)) {
                    if (key == "_css"){
                        comm.model.css = state[key];
                    } else {
                        comm.model.set(key, state[key]); 
                    }
                }
            }
            comm.model.id = comm.comm_id;
            comm.model.save();
            this.updating = false;
        }

        // Handle when a widget is closed.
        WidgetManager.prototype.handle_comm_closed = function (comm, msg) {
            for (var view_index in comm.model.views) {
                var view = comm.model.views[view_index];
                view.remove();
            }
        }

        // Handle when a msg status changes in the kernel.
        WidgetManager.prototype.handle_status = function (msg) {
            //execution_state : ('busy', 'idle', 'starting')
            if (msg.content.execution_state=='idle') {
                // Send buffer if this message caused another message to be
                // throttled.
                if (this.msg_throttle == --this.pending_msgs && 
                    this.msg_buffer.length > 0) {
                    var outputarea = this._get_msg_outputarea(msg);
                    var callbacks = this._make_callbacks(outputarea);
                    var data = {sync_method: 'patch', sync_data: this.msg_buffer};
                    comm.send(data, callbacks);   
                    this.pending_msgs++;
                    this.msg_buffer = {};
                }
            }
        }

        // Get the cell output area corresponding to the comm.
        WidgetManager.prototype._get_comm_outputarea = function (comm) {
            // TODO: get element from comm instead of guessing
            var cell = IPython.notebook.get_cell(IPython.notebook.get_selected_index())
            return cell.output_area;
        }

        // Get the cell output area corresponding to the msg_id.
        WidgetManager.prototype._get_msg_outputarea = function (msg) {
            // TODO: get element from msg_id instead of guessing
            // msg.parent_header.msg_id
            var cell = IPython.notebook.get_cell(IPython.notebook.get_selected_index())
            return cell.output_area;
        }

        // Build a callback dict.
        WidgetManager.prototype._make_callbacks = function (outputarea) {
            var callbacks = {};
            if (outputarea != null) {
                callbacks = {
                    iopub : {
                    status : $.proxy(this.handle_status, this),
                    output : $.proxy(outputarea.handle_output, outputarea),
                    clear_output : $.proxy(outputarea.handle_clear_output, outputarea)}
                };
            }
            return callbacks;
        }

        // Send widget state to python backend.
        WidgetManager.prototype.handle_sync = function (method, model, options) {
            var model_json = model.toJSON();

            // Only send updated state if the state hasn't been changed during an update.
            if (!this.updating) {
                // Create a callback for the output if the widget has an output area associate with it.
                var callbacks = this._make_callbacks(this._get_comm_outputarea(comm));
                var comm = model.comm;

                if (this.pending_msgs >= this.msg_throttle) {
                    // The throttle has been exceeded, buffer the current msg so
                    // it can be sent once the kernel has finished processing 
                    // some of the existing messages.
                    if (method=='patch') {
                        for (var attr in options.attrs) {
                            this.msg_buffer[attr] = options.attrs[attr];
                        }
                    } else {
                        this.msg_buffer = $.extend({}, model_json); // Copy
                    }
                } else {
                    // We haven't exceeded the throttle, send the message like 
                    // normal.  If this is a patch operation, just send the 
                    // changes.
                    var send_json = model_json;
                    if (method=='patch') {
                        send_json = {};
                        for (var attr in options.attrs) {
                            send_json[attr] = options.attrs[attr];
                        }
                    }
                    var data = {sync_method: method, sync_data: send_json};
                    comm.send(data, callbacks);    
                    this.pending_msgs++;
                }
            }
            
            // Since the comm is a one-way communication, assume the message 
            // arrived.
            return model_json;
        }

        IPython.WidgetManager = WidgetManager;
        IPython.WidgetModel = WidgetModel;
        IPython.WidgetView = WidgetView;

        IPython.notebook.widget_manager = new WidgetManager(IPython.notebook.kernel.comm_manager);    

    };
});
