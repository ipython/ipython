// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "underscore",
    "backbone",
    "jquery",
    "base/js/namespace"
], function (_, Backbone, $, IPython) {

    "use strict";

    var Loader = function (klass) {
        this.klass = klass;
        this._cb = [];
        this._ctx = [];

        this.after_loaded = function(cb, ctx) {
            if (this.klass) {
                cb.apply(ctx, [this.klass]);
            } else {
                this._cb.push(cb);
                this._ctx.push(cb);
            }
        }

        this.fire_loaded = function(klass) {
            this.klass = klass;
            for (var i=0; i<this._cb.length; i++) {
                this._cb[i].apply(this._ctx[i], [this.klass]);
            }
            this._cb = [];
            this._ctx = [];
        }
    };

    //--------------------------------------------------------------------
    // WidgetManager class
    //--------------------------------------------------------------------
    var WidgetManager = function (comm_manager, notebook) {
        // Public constructor
        WidgetManager._managers.push(this);

        // Attach a comm manager
        this.keyboard_manager = notebook.keyboard_manager;
        this.notebook = notebook;
        this.comm_manager = comm_manager;
        this._models = {}; /* Dictionary of model ids and model instances */

        // Register already-registered widget model types with the comm manager.
        var that = this;
        _.each(WidgetManager._model_types, function(model_type, model_name) {
            that.comm_manager.register_target(model_name, $.proxy(that._handle_comm_open, that));
        });

        // Custom widget loader
        this.comm_manager.register_target("manager", function(comm) {
            comm.on_msg(function(msg) {
                var data = msg.content.data;
                switch (data.target_type) {
                    case "widget_model":
                        WidgetManager._load_model(data.target_name, data.path);
                    case "widget_view":
                        WidgetManager._load_view(data.target_name, data.path);
                }
            });
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

    WidgetManager._load_model = function(target_name, mod) {
        // Loads a widget model module and registers it.
        var loader = new Loader();
        WidgetManager.register_widget_model(target_name, loader);
        require([mod], function(m) {
                loader.fire_loaded(m[target_name]);
            }, function(err) { console.log(err);
        });
    };

    WidgetManager._load_view = function(target_name, mod) {
        // Loads a widget view module and registers it.
        var loader = new Loader();
        WidgetManager.register_widget_view(target_name, loader);
        require([mod], function(m) {
                loader.fire_loaded(m[target_name]);
            }, function(err) { console.log(err);
        });
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
            this.create_view(model, {cell: cell, callback: function(view) {
                if (view === null) {
                    console.error("View creation failed", model);
                }
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
        var errback = options.errback || function(err) {console.log(err);};

        var instantiate_view = function(ViewType) {
            if (ViewType) {
                // If a view is passed into the method, use that view's cell as
                // the cell for the view that is created.
                options = options || {};
                if (options.parent !== undefined) {
                    options.cell = options.parent.options.cell;
                }

                // Create and render the view...
                var parameters = {model: model, options: options};
                var view = new ViewType(parameters);
                view.render();
                model.on('destroy', view.remove, view);
                options.callback(view);
            } else {
                errback({unknown_view: true, view_name: view_name });
            }
        };
        var loader = WidgetManager._view_types[view_name];
        loader.after_loaded(instantiate_view);
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
        var that = this;
        var model_id = comm.comm_id;
        var model_name = msg.content.target_name;
        var loader = WidgetManager._model_types[model_name];
        loader.after_loaded(function(ModelType) {
             var widget_model = new ModelType(this, model_id, comm);
             widget_model.on('comm:close', function () {
                 delete that._models[model_id];
             });
             this._models[model_id] = widget_model;
        }, this);
    };

    // Backwards compatability.
    IPython.WidgetManager = WidgetManager;

    return {'WidgetManager': WidgetManager, 'Loader': Loader};
});
