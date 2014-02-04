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
            ], function (_, Backbone) {

        //--------------------------------------------------------------------
        // WidgetManager class
        //--------------------------------------------------------------------
        var WidgetManager = function (comm_manager) {
            // Public constructor
            WidgetManager._managers.push(this);

            // Attach a comm manager to the 
            this.comm_manager = comm_manager;
            this._models = {}; /* Dictionary of model ids and model instances */

            // Register already-registered widget model types with the comm manager.
            var that = this;
            _.each(WidgetManager._model_types, function(model_type, model_name) {
                that.comm_manager.register_target(model_name, $.proxy(that._handle_comm_open, that));
            });
        };

        //--------------------------------------------------------------------
        // Class level
        //--------------------------------------------------------------------
        WidgetManager._model_types = {}; /* Dictionary of model type names (target_name) and model types. */
        WidgetManager._view_types = {}; /* Dictionary of view names and view types. */
        WidgetManager._managers = []; /* List of widget managers */

        WidgetManager.register_widget_model = function (model_name, model_type) {
            // Registers a widget model by name.
            WidgetManager._model_types[model_name] = model_type;

            // Register the widget with the comm manager.  Make sure to pass this object's context
            // in so `this` works in the call back.
            _.each(WidgetManager._managers, function(instance, i) {
                if (instance.comm_manager !== null) {
                    instance.comm_manager.register_target(model_name, $.proxy(instance._handle_comm_open, instance));
                }
            });
        };

        WidgetManager.register_widget_view = function (view_name, view_type) {
            // Registers a widget view by name.
            WidgetManager._view_types[view_name] = view_type;
        };

        //--------------------------------------------------------------------
        // Instance level
        //--------------------------------------------------------------------
        WidgetManager.prototype.display_view = function(msg, model) {
            // Displays a view for a particular model.
            var cell = this.get_msg_cell(msg.parent_header.msg_id);
            if (cell === null) {
                console.log("Could not determine where the display" + 
                    " message was from.  Widget will not be displayed");
            } else {
                var view = this.create_view(model, {cell: cell});
                if (view === null) {
                    console.error("View creation failed", model);
                }
                if (cell.widget_subarea) {
                    cell.widget_area.show();
                    this._handle_display_view(view);
                    cell.widget_subarea.append(view.$el);
                }
            }
        };

        WidgetManager.prototype._handle_display_view = function (view) {
            // Have the IPython keyboard manager disable its event
            // handling so the widget can capture keyboard input.
            // Note, this is only done on the outer most widgets.
            IPython.keyboard_manager.register_events(view.$el);
            
            if (view.additional_elements) {
                for (var i = 0; i < view.additional_elements.length; i++) {
                    IPython.keyboard_manager.register_events(view.additional_elements[i]);
                }
            } 
        };

        WidgetManager.prototype.create_view = function(model, options, view) {
            // Creates a view for a particular model.
            var view_name = model.get('_view_name');
            var ViewType = WidgetManager._view_types[view_name];
            if (ViewType) {

                // If a view is passed into the method, use that view's cell as
                // the cell for the view that is created.
                options = options || {};
                if (view !== undefined) {
                    options.cell = view.options.cell;
                }

                // Create and render the view...
                var parameters = {model: model, options: options};
                view = new ViewType(parameters);
                view.render();
                model.views.push(view);
                model.on('destroy', view.remove, view);
                return view;
            }
            return null;
        };

        WidgetManager.prototype.get_msg_cell = function (msg_id) {
            var cell = null;
            // First, check to see if the msg was triggered by cell execution.
            if (IPython.notebook) {
                cell = IPython.notebook.get_msg_cell(msg_id);
            }
            if (cell !== null) {
                return cell;
            }
            // Second, check to see if a get_cell callback was defined
            // for the message.  get_cell callbacks are registered for
            // widget messages, so this block is actually checking to see if the
            // message was triggered by a widget.
            var kernel = this.comm_manager.kernel;
            if (kernel) {
                var callbacks = kernel.get_callbacks_for_msg(msg_id);
                if (callbacks && callbacks.iopub &&
                    callbacks.iopub.get_cell !== undefined) {
                    return callbacks.iopub.get_cell();
                }
            }
            
            // Not triggered by a cell or widget (no get_cell callback 
            // exists).
            return null;
        };

        WidgetManager.prototype.callbacks = function (view) {
            // callback handlers specific a view
            var callbacks = {};
            if (view && view.options.cell) {

                // Try to get output handlers
                var cell = view.options.cell;
                var handle_output = null;
                var handle_clear_output = null;
                if (cell.output_area) {
                    handle_output = $.proxy(cell.output_area.handle_output, cell.output_area);
                    handle_clear_output = $.proxy(cell.output_area.handle_clear_output, cell.output_area);
                }

                // Create callback dict using what is known
                var that = this;
                callbacks = {
                    iopub : {
                        output : handle_output,
                        clear_output : handle_clear_output,

                        // Special function only registered by widget messages.
                        // Allows us to get the cell for a message so we know
                        // where to add widgets if the code requires it.
                        get_cell : function () {
                            return cell;
                        },
                    },
                };
            }
            return callbacks;
        };

        WidgetManager.prototype.get_model = function (model_id) {
            // Look-up a model instance by its id.
            var model = this._models[model_id];
            if (model !== undefined && model.id == model_id) {
                return model;
            }
            return null;
        };

        WidgetManager.prototype._handle_comm_open = function (comm, msg) {
            // Handle when a comm is opened.
            var model_id = comm.comm_id;
            var widget_type_name = msg.content.target_name;
            var widget_model = new WidgetManager._model_types[widget_type_name](this, model_id, comm);
            this._models[model_id] = widget_model;
        };
        
        IPython.WidgetManager = WidgetManager;
        return IPython.WidgetManager;
    });
}());
