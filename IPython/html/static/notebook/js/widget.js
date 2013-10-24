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
define(["../../components/underscore/underscore-min.js",
         "../../components/backbone/backbone-min.js",
        ], function(){

    // Only run once on a notebook.
    if (IPython.notebook.widget_manager == undefined) {

        //--------------------------------------------------------------------
        // WidgetModel class
        //--------------------------------------------------------------------
        var WidgetModel = Backbone.Model.extend({
            constructor: function(comm_manager, comm, widget_view_types) {
                this.comm_manager = comm_manager;
                this.widget_view_types = widget_view_types;
                this.pending_msgs = 0;
                this.msg_throttle = 3;
                this.msg_buffer = {};
                this.views = {};

                // Remember comm associated with the model.
                this.comm = comm;
                comm.model = this;

                // Hook comm messages up to model.
                comm.on_close($.proxy(this.handle_comm_closed, this));
                comm.on_msg($.proxy(this.handle_comm_msg, this));

                return Backbone.Model.apply(this);
            },


            update_other_views: function(caller) {
                this.last_modified_view = caller;
                this.save(this.changedAttributes(), {patch: true});

                for (var cell_index in this.views) {
                    var view = this.views[cell_index];
                    if (view !== caller) {
                        view.update();    
                    }
                }
            },


            handle_status: function (output_area, msg) {
                //execution_state : ('busy', 'idle', 'starting')
                if (msg.content.execution_state=='idle') {
                    
                    // Send buffer if this message caused another message to be
                    // throttled.
                    if (this.msg_throttle == this.pending_msgs && 
                        this.msg_buffer.length > 0) {
                        
                        var output_area = this._get_msg_output_area(msg);
                        var callbacks = this._make_callbacks(output_area);
                        var data = {sync_method: 'patch', sync_data: this.msg_buffer};
                        comm.send(data, callbacks);   
                        this.msg_buffer = {};
                    } else {

                        // Only decrease the pending message count if the buffer
                        // doesn't get flushed (sent).
                        --this.pending_msgs;
                    }
                }
            },


            // Custom syncronization logic.
            handle_sync: function (method, options) {
                var model_json = this.toJSON();

                // Only send updated state if the state hasn't been changed 
                // during an update.
                if (!this.updating) {
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
                        var output_area = this._get_view_output_area(this.last_modified_view);
                        var callbacks = this._make_callbacks(output_area);
                        this.comm.send(data, callbacks);    
                        this.pending_msgs++;
                    }
                }
                
                // Since the comm is a one-way communication, assume the message 
                // arrived.
                return model_json;
            },


            // Handle incomming comm msg.
            handle_comm_msg: function (msg) {
                var method = msg.content.data.method;
                switch (method){
                    case 'display':

////////////////////////// TODO: Get cell index via currently executing cell.
                        var cell_index = IPython.notebook.get_selected_index()-1;

                        this.display_view(msg.content.data.view_name, 
                            msg.content.data.parent,
                            cell_index);
                        break;
                    case 'update':
                        this.handle_update(msg.content.data.state);
                        break;
                }
            },


            // Handle when a widget is updated via the python side.
            handle_update: function (state) {
                this.updating = true;
                try {
                    for (var key in state) {
                        if (state.hasOwnProperty(key)) {
                            if (key == "_css"){
                                this.css = state[key];
                            } else {
                                this.set(key, state[key]); 
                            }
                        }
                    }
                    this.id = this.comm.comm_id;
                    this.save();
                } finally {
                    this.updating = false;
                }
            },


            // Handle when a widget is closed.
            handle_comm_closed: function (msg) {
                for (var cell_index in this.views) {
                    var view = this.views[cell_index];
                    view.remove();
                }
            },


            // Create view that represents the model.
            display_view: function (view_name, parent_comm_id, cell_index) {
                var view = new this.widget_view_types[view_name]({model: this});
                view.render();
                this.views[cell_index] = view;
                view.cell_index = cell_index;

                // Handle when the view element is remove from the page.
                var that = this;
                view.$el.on("remove", function(){ 
                    var index = that.views.indexOf(view);
                    if (index > -1) {
                        that.views.splice(index, 1);
                    }
                    view.remove(); // Clean-up view 

                    // Close the comm if there are no views left.
                    if (that.views.length()==0) {
                        that.comm.close();     
                    }
                });

                var displayed = false;
                if (parent_comm_id != undefined) {
                    var parent_comm = this.comm_manager.comms[parent_comm_id];
                    var parent_model = parent_comm.model;
                    var parent_view = parent_model.views[cell_index];
                    if (parent_view.display_child != undefined) {
                        parent_view.display_child(view);
                        displayed = true;
                    }
                }

                if (!displayed) {
                    // No parent view is defined or exists.  Add the view's 
                    // element to cell's widget div.
                    var cell = IPython.notebook.get_cell(cell_index);
                    cell.element.find('.widget_area').find('.widget_subarea')
                        .append(view.$el)
                        .parent().show(); // Show the widget_area (parent of widget_subarea)
                
                }

                // Update the view based on the model contents.
                view.update();
            },


            // Build a callback dict.
            _make_callbacks: function (output_area) {
                var callbacks = {};
                if (output_area != null) {
                    var that = this;
                    callbacks = {
                        iopub : {
                            output : $.proxy(output_area.handle_output, output_area),
                            clear_output : $.proxy(output_area.handle_clear_output, output_area),
                            status : function(msg){
                                that.handle_status(output_area, msg);
                            },
                        },
                    };
                }
                return callbacks;
            },


            // Get the cell output area corresponding to the view.
            _get_view_output_area: function (view) {
                return this._get_cell_output_area(view.cell_index);
            },


            // Get the cell output area corresponding to the cell id.
            _get_cell_output_area: function (cell_id) {
                var cell = IPython.notebook.get_cell(cell_id)
                return cell.output_area;
            },
        });


        //--------------------------------------------------------------------
        // WidgetView class
        //--------------------------------------------------------------------
        var WidgetView = Backbone.View.extend({
            
            initialize: function() {
                this.model.on('change',this.update,this);
            },
            
            update: function() {
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
        var WidgetManager = function(comm_manager){
            this.comm_manager = comm_manager;
            this.widget_model_types = {};
            this.widget_view_types = {};
            
            var that = this;
            Backbone.sync = function(method, model, options, error) {
                var result = model.handle_sync(method, options);
                if (options.success) {
                  options.success(result);
                }
            }; 
        }


        WidgetManager.prototype.register_widget_model = function (widget_model_name, widget_model_type) {
            // Register the widget with the comm manager.  Make sure to pass this object's context
            // in so `this` works in the call back.
            this.comm_manager.register_target(widget_model_name, $.proxy(this.handle_com_open, this));
            this.widget_model_types[widget_model_name] = widget_model_type;
        }


        WidgetManager.prototype.register_widget_view = function (widget_view_name, widget_view_type) {
            this.widget_view_types[widget_view_name] = widget_view_type;
        }


        WidgetManager.prototype.handle_com_open = function (comm, msg) {
            var widget_type_name = msg.content.target_name;
            var widget_model = new this.widget_model_types[widget_type_name](this.comm_manager, comm, this.widget_view_types);
        }


        //--------------------------------------------------------------------
        // Init code
        //--------------------------------------------------------------------
        IPython.WidgetManager = WidgetManager;
        IPython.WidgetModel = WidgetModel;
        IPython.WidgetView = WidgetView;

        IPython.notebook.widget_manager = new WidgetManager(IPython.notebook.kernel.comm_manager);    

    };
});
