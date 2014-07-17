// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "underscore",
    "backbone",
    "base/js/namespace"
], function (_, Backbone, IPython) {

    //--------------------------------------------------------------------
    // WidgetManager class
    //--------------------------------------------------------------------
    var WidgetManager = function (options) {
        // Public constructor
        WidgetManager._managers.push(this);

        this.register_target = options.register_target;
        this.get_msg_cell = options.get_msg_cell;
        this.notebook_display_view = options.display_view;
        this.show_widgetarea = options.show_widgetarea;

        this._models = {}; /* Dictionary of model ids and model instances */

        // Register already-registered widget model types with the comm manager.
        var that = this;
        _.each(WidgetManager._model_types, function(model_type, model_name) {
            that.register_target(model_name, $.proxy(that._handle_comm_open, that));
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
            if (instance.register_target !== null) {
                instance.register_target(model_name, $.proxy(instance._handle_comm_open, instance));
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
        var that = this;
        this.get_msg_cell(msg.parent_header.msg_id, function (cell) {
            if (cell === null) {
                console.log("Could not determine where the display" + 
                    " message was from.  Widget will not be displayed");
            } else {
                var view = that.create_view(model, {cell: cell});
                if (view === null) {
                    console.error("View creation failed", model);
                }
                that.notebook_display_view(cell, view);
                view.trigger('displayed');
            }
        });
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
            model.on('destroy', view.remove, view);
            return view;
        }
        return null;
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
        var widget_type_name = msg.content.target_name;
        var widget_model = new WidgetManager._model_types[widget_type_name](this, model_id, comm);
        widget_model.on('comm:close', function () {
          delete that._models[model_id];
        });
        this._models[model_id] = widget_model;
    };

    // Backwards compatability.
    IPython.WidgetManager = WidgetManager;

    return {'WidgetManager': WidgetManager};
});
