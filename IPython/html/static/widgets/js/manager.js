// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "underscore",
    "backbone",
    "jquery",
    "base/js/namespace"
], function (_, Backbone, $, IPython) {
    "use strict";
    //--------------------------------------------------------------------
    // WidgetManager class
    //--------------------------------------------------------------------
    var WidgetManager = function (comm_manager, notebook) {
        // Public constructor
        WidgetManager._managers.push(this);

        // Attach a comm manager to the 
        this.keyboard_manager = notebook.keyboard_manager;
        this.notebook = notebook;
        this.comm_manager = comm_manager;
        this._models = {}; /* Dictionary of model ids and model instances */

        // Register with the comm manager.
        this.comm_manager.register_target('ipython.widget', $.proxy(this._handle_comm_open, this));
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
            var that = this;
            this.create_view(model, {cell: cell, success: function(view) {
                that._handle_display_view(view);
                if (cell.widget_subarea) {
                    cell.widget_subarea.append(view.$el);
                }
                view.trigger('displayed');
            }});
        }
    };

    WidgetManager.prototype._handle_display_view = function (view) {
        // Have the IPython keyboard manager disable its event
        // handling so the widget can capture keyboard input.
        // Note, this is only done on the outer most widgets.
        if (this.keyboard_manager) {
            this.keyboard_manager.register_events(view.$el);
        
        if (view.additional_elements) {
            for (var i = 0; i < view.additional_elements.length; i++) {
                    this.keyboard_manager.register_events(view.additional_elements[i]);
            }
        } 
        }
    };
    

    WidgetManager.prototype.create_view = function(model, options) {
        // Creates a view for a particular model.
        
        var view_name = model.get('_view_name');
        var view_mod = model.get('_view_module');
        var options = options || {};

        return new Promise(function(resolve, reject) {
            var instantiate_view = function(ViewType) {
                if (ViewType === undefined) {
                    reject(Error("Unknown view, module: "+view_mod+", view: "+view_name));
                }

                // If a view is passed into the method, use that view's cell as
                // the cell for the view that is created.
                if (options.parent !== undefined) {
                    options.cell = options.parent.options.cell;
                }

                // Create and render the view...
                var parameters = {model: model, options: options};
                var view = new ViewType(parameters);
                view.render();
                view.listenTo(model, 'destroy', view.remove);
                resolve(view);
            };

            
            if (view_mod) {
                require([view_mod], function(module) {
                    instantiate_view(module[view_name]);
                }, reject);
            } else {
                instantiate_view(WidgetManager._view_types[view_name]);
            }
        }
    };

    WidgetManager.prototype.get_msg_cell = function (msg_id) {
        var cell = null;
        // First, check to see if the msg was triggered by cell execution.
        if (this.notebook) {
            cell = this.notebook.get_msg_cell(msg_id);
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

            // Create callback dictionary using what is known
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
        this.create_model({
            model_name: msg.content.data.model_name, 
            model_module: msg.content.data.model_module, 
            comm: comm});
    };

    WidgetManager.prototype.create_model = function (options) {
        // Create and return a promise to create a new widget model.
        //
        // Minimally, one must provide the model_name and widget_class
        // parameters to create a model from Javascript.
        //
        // Example
        // --------
        // JS:
        // IPython.notebook.kernel.widget_manager.create_model({
        //      model_name: 'WidgetModel', 
        //      widget_class: 'IPython.html.widgets.widget_int.IntSlider',
        //      init_state_callback: function(model) { console.log('Create success!', model); }});
        //
        // Parameters
        // ----------
        // options: dictionary
        //  Dictionary of options with the following contents:
        //      model_name: string
        //          Target name of the widget model to create.
        //      model_module: (optional) string
        //          Module name of the widget model to create.
        //      widget_class: (optional) string
        //          Target name of the widget in the back-end.
        //      comm: (optional) Comm
        //      init_state_callback: (optional) callback
        //          Called when the first state push from the back-end is 
        //          recieved.  Allows you to modify the model after it's
        //          complete state is filled and synced.

        // Create a comm if it wasn't provided.
        var comm = options.comm;
        if (!comm) {
            comm = this.comm_manager.new_comm('ipython.widget', {'widget_class': options.widget_class});
        }

        return new Promise(function(resolve, reject) {
            // Create a new model that is connected to the comm.
            var that = this;
            var instantiate_model = function(ModelType) {
                if (ModelType === undefined) {
                    reject(Error("Error creating widget model: " + widget_type_name
                                 + " not found in " + widget_module));
                }
                var model_id = comm.comm_id;
                var widget_model = new ModelType(that, model_id, comm, options.init_state_callback);
                widget_model.once('comm:close', function () {
                    delete that._models[model_id];
                });
                that._models[model_id] = widget_model;
                resolve(widget_model);
            };
            
            // Get the model type using require or through the registry.
            var widget_type_name = options.model_name;
            var widget_module = options.model_module;
            if (widget_module) {                
                // Load the module containing the widget model
                require([widget_module], function(mod) {
                    instantiate_model(mod[widget_type_name]);
                }, reject);
            } else {
                // No module specified, load from the global models registry
                instantiate_model(WidgetManager._model_types[widget_type_name]);
            }
        }
    };

    // Backwards compatability.
    IPython.WidgetManager = WidgetManager;

    return {'WidgetManager': WidgetManager};
});
