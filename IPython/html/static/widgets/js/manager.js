// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "underscore",
    "backbone",
    "jquery",
    "base/js/utils",
    "base/js/namespace",
], function (_, Backbone, $, utils, IPython) {
    "use strict";
    //--------------------------------------------------------------------
    // WidgetManager class
    //--------------------------------------------------------------------
    var WidgetManager = function (comm_manager, notebook) {
        /**
         * Public constructor
         */
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
        /**
         * Displays a view for a particular model.
         */
        var that = this;
        var cell = this.get_msg_cell(msg.parent_header.msg_id);
        if (cell === null) {
            return Promise.reject(new Error("Could not determine where the display" +
                                            " message was from.  Widget will not be displayed"));
        } else if (cell.widget_subarea) {
            var dummy = $('<div />');
            cell.widget_subarea.append(dummy);
            return this.create_view(model, {cell: cell}).then(
                function(view) {
                    that._handle_display_view(view);
                    dummy.replaceWith(view.$el);
                    view.trigger('displayed');
                    return view;
                }).catch(utils.reject('Could not display view', true));
        }
    };

    WidgetManager.prototype._handle_display_view = function (view) {
        /**
         * Have the IPython keyboard manager disable its event
         * handling so the widget can capture keyboard input.
         * Note, this is only done on the outer most widgets.
         */
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
        /**
         * Creates a promise for a view of a given model
         *
         * Make sure the view creation is not out of order with 
         * any state updates.
         */
        model.state_change = model.state_change.then(function() {
            
            return utils.load_class(model.get('_view_name'), model.get('_view_module'),
            WidgetManager._view_types).then(function(ViewType) {

                // If a view is passed into the method, use that view's cell as
                // the cell for the view that is created.
                options = options || {};
                if (options.parent !== undefined) {
                    options.cell = options.parent.options.cell;
                }
                // Create and render the view...
                var parameters = {model: model, options: options};
                var view = new ViewType(parameters);
                view.listenTo(model, 'destroy', view.remove);
                return Promise.resolve(view.render()).then(function() {return view;});
            }).catch(utils.reject("Couldn't create a view for model id '" + String(model.id) + "'", true));
        });
        return model.state_change;
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
        /**
         * callback handlers specific a view
         */
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
        /**
         * Get a promise for a model by model id.
         */
        return this._models[model_id];
    };

    WidgetManager.prototype._handle_comm_open = function (comm, msg) {
        /**
         * Handle when a comm is opened.
         */
        return this.create_model({
            model_name: msg.content.data.model_name, 
            model_module: msg.content.data.model_module, 
            comm: comm}).catch(utils.reject("Couldn't create a model.", true));
    };

    WidgetManager.prototype.create_model = function (options) {
        /**
         * Create and return a promise for a new widget model
         *
         * Minimally, one must provide the model_name and widget_class
         * parameters to create a model from Javascript.
         *
         * Example
         * --------
         * JS:
         * IPython.notebook.kernel.widget_manager.create_model({
         *      model_name: 'WidgetModel', 
         *      widget_class: 'IPython.html.widgets.widget_int.IntSlider'})
         *      .then(function(model) { console.log('Create success!', model); },
         *      $.proxy(console.error, console));
         *
         * Parameters
         * ----------
         * options: dictionary
         *  Dictionary of options with the following contents:
         *      model_name: string
         *          Target name of the widget model to create.
         *      model_module: (optional) string
         *          Module name of the widget model to create.
         *      widget_class: (optional) string
         *          Target name of the widget in the back-end.
         *      comm: (optional) Comm
         *
         * Create a comm if it wasn't provided.
         */
        var comm = options.comm;
        if (!comm) {
            comm = this.comm_manager.new_comm('ipython.widget', {'widget_class': options.widget_class});
        }

        var that = this;
        var model_id = comm.comm_id;
        var model_promise =  utils.load_class(options.model_name, options.model_module, WidgetManager._model_types)
            .then(function(ModelType) {
                var widget_model = new ModelType(that, model_id, comm);
                widget_model.once('comm:close', function () {
                    delete that._models[model_id];
                });
                return widget_model;

            }, function(error) {
                delete that._models[model_id];
                var wrapped_error = new utils.WrappedError("Couldn't create model", error);
                return Promise.reject(wrapped_error);
            });
        this._models[model_id] = model_promise;
        return model_promise;
    };

    // Backwards compatibility.
    IPython.WidgetManager = WidgetManager;

    return {'WidgetManager': WidgetManager};
});
