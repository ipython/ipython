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
    define(["components/underscore/underscore-min",
             "components/backbone/backbone-min",
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

            // Register already register widget model types with the comm manager.
            for (var widget_model_name in this.widget_model_types) {
                this.comm_manager.register_target(widget_model_name, $.proxy(this._handle_com_open, this));
            }
        };


        WidgetManager.prototype.register_widget_model = function (widget_model_name, widget_model_type) {
            // Register the widget with the comm manager.  Make sure to pass this object's context
            // in so `this` works in the call back.
            if (this.comm_manager !== null) {
                this.comm_manager.register_target(widget_model_name, $.proxy(this._handle_com_open, this));
            }
            this.widget_model_types[widget_model_name] = widget_model_type;
        };


        WidgetManager.prototype.register_widget_view = function (widget_view_name, widget_view_type) {
            this.widget_view_types[widget_view_name] = widget_view_type;
        };


        WidgetManager.prototype.get_msg_cell = function (msg_id) {
            if (IPython.notebook !== undefined && IPython.notebook !== null) {
                return IPython.notebook.get_msg_cell(msg_id);
            }
        };


        WidgetManager.prototype.get_model = function (widget_id) {
            var model = this._model_instances[widget_id];
            if (model !== undefined && model.id == widget_id) {
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


        WidgetManager.prototype._handle_com_open = function (comm, msg) {
            var widget_type_name = msg.content.target_name;
            var widget_model = new this.widget_model_types[widget_type_name](this, comm.comm_id, comm);
            this._model_instances[comm.comm_id] = widget_model;
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