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

(function () {
    "use strict";

    // Use require.js 'define' method so that require.js is intelligent enough to
    // syncronously load everything within this file when it is being 'required' 
    // elsewhere.
    define(["underscore",
             "backbone",
            ], function (underscore, backbone) {

        //--------------------------------------------------------------------
        // WidgetManager class
        //--------------------------------------------------------------------
        var WidgetManager = function () {
            this.comm_manager = null;
            this.widget_model_types = {};
            this.widget_view_types = {};
            this._model_instances = {};
            
            Backbone.sync = function (method, model, options, error) {
                var result = model._handle_sync(method, options);
                if (options.success) {
                  options.success(result);
                }
            }; 
        };


        WidgetManager.prototype.attach_comm_manager = function (comm_manager) {
            this.comm_manager = comm_manager;

            // Register already-registered widget model types with the comm manager.
            for (var widget_model_name in this.widget_model_types) {
                this.comm_manager.register_target(widget_model_name, $.proxy(this._handle_comm_open, this));
            }
        };


        WidgetManager.prototype.register_widget_model = function (widget_model_name, widget_model_type) {
            // Register the widget with the comm manager.  Make sure to pass this object's context
            // in so `this` works in the call back.
            if (this.comm_manager !== null) {
                this.comm_manager.register_target(widget_model_name, $.proxy(this._handle_comm_open, this));
            }
            this.widget_model_types[widget_model_name] = widget_model_type;
        };


        WidgetManager.prototype.register_widget_view = function (widget_view_name, widget_view_type) {
            this.widget_view_types[widget_view_name] = widget_view_type;
        };


        WidgetManager.prototype.handle_msg = function(msg, model) {
            var method = msg.content.data.method;
            switch (method) {
            case 'display':
                var cell = this.get_msg_cell(msg.parent_header.msg_id);
                if (cell === null) {
                console.log("Could not determine where the display" + 
                        " message was from.  Widget will not be displayed");
                } else {
                var view = this.create_view(model, 
                                msg.content.data.view_name, cell);
                if (view !== undefined 
                    && cell.widget_subarea !== undefined 
                    && cell.widget_subarea !== null) {
                                cell.widget_area.show();
                                cell.widget_subarea.append(view.$el);
                }
                }
                break;
            }
        }

        WidgetManager.prototype.create_view = function(model, view_name, cell) {
            view_name = view_name || model.get('default_view_name');
            var ViewType = this.widget_view_types[view_name];
            if (ViewType !== undefined && ViewType !== null) {
                var view = new ViewType({model: model, widget_manager: this, cell: cell});
                view.render();
                model.views.push(view);
                model.on('destroy', view.remove, view);
                /*
                    // TODO: handle view deletion.  Don't forget to delete child views
                    var that = this;
                    view.$el.on("remove", function () { 
                        var index = that.views.indexOf(view);
                        if (index > -1) {
                            that.views.splice(index, 1);
                        }
                        view.remove(); // Clean-up view 

                        // Close the comm if there are no views left.
                        if (that.views.length() === 0) {
                //trigger comm close event?
                            }

                    
                            if (that.comm !== undefined) {
                                that.comm.close();
                                delete that.comm.model; // Delete ref so GC will collect widget model.
                                delete that.comm;
                            }
                            delete that.model_id; // Delete id from model so widget manager cleans up.
                        });
                */
                return view;
            }
        },

        WidgetManager.prototype.get_msg_cell = function (msg_id) {
        var cell = null;
            // First, check to see if the msg was triggered by cell execution.
            if (IPython.notebook !== undefined && IPython.notebook !== null) {
                cell = IPython.notebook.get_msg_cell(msg_id);
            }
        if (cell !== null) {
        return cell
        }
            // Second, check to see if a get_cell callback was defined
            // for the message.  get_cell callbacks are registered for
            // widget messages, so this block is actually checking to see if the
            // message was triggered by a widget.
            var kernel = this.get_kernel();
            if (kernel !== undefined && kernel !== null) {
                var callbacks = kernel.get_callbacks_for_msg(msg_id);
                if (callbacks !== undefined && 
                    callbacks.iopub !== undefined && 
                    callbacks.iopub.get_cell !== undefined) {

                    return callbacks.iopub.get_cell();
                }    
            }
            
            // Not triggered by a cell or widget (no get_cell callback 
            // exists).
            return null;
        };


        WidgetManager.prototype.get_model = function (model_id) {
            var model = this._model_instances[model_id];
            if (model !== undefined && model.id == model_id) {
                return model;
            }
            return null;
        };


        WidgetManager.prototype.get_kernel = function () {
            if (this.comm_manager === null) {
                return null;
            } else {
                return this.comm_manager.kernel;
            }
        };


        WidgetManager.prototype.on_create_widget = function (callback) {
            this._create_widget_callback = callback;
        };


        WidgetManager.prototype._handle_create_widget = function (widget_model) {
            if (this._create_widget_callback) {
                try {
                    this._create_widget_callback(widget_model);
                } catch (e) {
                    console.log("Exception in WidgetManager callback", e, widget_model);
                }
            }
        };


        WidgetManager.prototype._handle_comm_open = function (comm, msg) {
            var widget_type_name = msg.content.target_name;
            var widget_model = new this.widget_model_types[widget_type_name](this, comm.comm_id, comm);
            this._model_instances[comm.comm_id] = widget_model; // comm_id == model_id
            this._handle_create_widget(widget_model);
        };
        
        //--------------------------------------------------------------------
        // Init code
        //--------------------------------------------------------------------
        IPython.WidgetManager = WidgetManager;
        if (IPython.widget_manager === undefined || IPython.widget_manager === null) {
            IPython.widget_manager = new WidgetManager();    
        }

        return IPython.widget_manager;
    });
}());
