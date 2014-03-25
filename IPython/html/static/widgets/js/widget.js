//----------------------------------------------------------------------------
//  Copyright (C) 2013 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Base Widget Model and View classes
//============================================================================

/**
 * @module IPython
 * @namespace IPython
 **/

define(["widgets/js/manager",
        "underscore",
        "backbone"], 
function(WidgetManager, _, Backbone){

    var WidgetModel = Backbone.Model.extend({
        constructor: function (widget_manager, model_id, comm) {
            // Constructor
            //
            // Creates a WidgetModel instance.
            //
            // Parameters
            // ----------
            // widget_manager : WidgetManager instance
            // model_id : string
            //      An ID unique to this model.
            // comm : Comm instance (optional)
            this.widget_manager = widget_manager;
            this._buffered_state_diff = {};
            this.pending_msgs = 0;
            this.msg_buffer = null;
            this.key_value_lock = null;
            this.id = model_id;
            this.views = [];

            if (comm !== undefined) {
                // Remember comm associated with the model.
                this.comm = comm;
                comm.model = this;

                // Hook comm messages up to model.
                comm.on_close($.proxy(this._handle_comm_closed, this));
                comm.on_msg($.proxy(this._handle_comm_msg, this));
            }
            return Backbone.Model.apply(this);
        },

        send: function (content, callbacks) {
            // Send a custom msg over the comm.
            if (this.comm !== undefined) {
                var data = {method: 'custom', content: content};
                this.comm.send(data, callbacks);
                this.pending_msgs++;
            }
        },

        _handle_comm_closed: function (msg) {
            // Handle when a widget is closed.
            this.trigger('comm:close');
            delete this.comm.model; // Delete ref so GC will collect widget model.
            delete this.comm;
            delete this.model_id; // Delete id from model so widget manager cleans up.
            _.each(this.views, function(view, i) {
                view.remove();
            });
        },

        _handle_comm_msg: function (msg) {
            // Handle incoming comm msg.
            var method = msg.content.data.method;
            switch (method) {
                case 'update':
                    this.apply_update(msg.content.data.state);
                    break;
                case 'custom':
                    this.trigger('msg:custom', msg.content.data.content);
                    break;
                case 'display':
                    this.widget_manager.display_view(msg, this);
                    this.trigger('displayed');
                    break;
            }
        },

        apply_update: function (state) {
            // Handle when a widget is updated via the python side.
            var that = this;
            _.each(state, function(value, key) {
                that.key_value_lock = [key, value];
                try {
                    WidgetModel.__super__.set.apply(that, [key, that._unpack_models(value)]);
                } finally {
                    that.key_value_lock = null;
                }
            });
        },

        _handle_status: function (msg, callbacks) {
            // Handle status msgs.

            // execution_state : ('busy', 'idle', 'starting')
            if (this.comm !== undefined) {
                if (msg.content.execution_state ==='idle') {
                    // Send buffer if this message caused another message to be
                    // throttled.
                    if (this.msg_buffer !== null &&
                        (this.get('msg_throttle') || 3) === this.pending_msgs) {
                        var data = {method: 'backbone', sync_method: 'update', sync_data: this.msg_buffer};
                        this.comm.send(data, callbacks);
                        this.msg_buffer = null;
                    } else {
                        --this.pending_msgs;
                    }
                }
            }
        },

        callbacks: function(view) {
            // Create msg callbacks for a comm msg.
            var callbacks = this.widget_manager.callbacks(view);

            if (callbacks.iopub === undefined) {
                callbacks.iopub = {};
            }

            var that = this;
            callbacks.iopub.status = function (msg) {
                that._handle_status(msg, callbacks);
            };
            return callbacks;
        },

        set: function(key, val, options) {
            // Set a value.
            var return_value = WidgetModel.__super__.set.apply(this, arguments);

            // Backbone only remembers the diff of the most recent set()
            // operation.  Calling set multiple times in a row results in a 
            // loss of diff information.  Here we keep our own running diff.
            this._buffered_state_diff = $.extend(this._buffered_state_diff, this.changedAttributes() || {});
            return return_value;
        },

        sync: function (method, model, options) {
            // Handle sync to the back-end.  Called when a model.save() is called.

            // Make sure a comm exists.
            var error = options.error || function() {
                console.error('Backbone sync error:', arguments);
            };
            if (this.comm === undefined) {
                error();
                return false;
            }

            // Delete any key value pairs that the back-end already knows about.
            var attrs = (method === 'patch') ? options.attrs : model.toJSON(options);
            if (this.key_value_lock !== null) {
                var key = this.key_value_lock[0];
                var value = this.key_value_lock[1];
                if (attrs[key] === value) {
                    delete attrs[key];
                }
            }

            // Only sync if there are attributes to send to the back-end.
            attrs = this._pack_models(attrs);
            if (_.size(attrs) > 0) {

                // If this message was sent via backbone itself, it will not
                // have any callbacks.  It's important that we create callbacks
                // so we can listen for status messages, etc...
                var callbacks = options.callbacks || this.callbacks();

                // Check throttle.
                if (this.pending_msgs >= (this.get('msg_throttle') || 3)) {
                    // The throttle has been exceeded, buffer the current msg so
                    // it can be sent once the kernel has finished processing 
                    // some of the existing messages.
                    
                    // Combine updates if it is a 'patch' sync, otherwise replace updates
                    switch (method) {
                        case 'patch':
                            this.msg_buffer = $.extend(this.msg_buffer || {}, attrs);
                            break;
                        case 'update':
                        case 'create':
                            this.msg_buffer = attrs;
                            break;
                        default:
                            error();
                            return false;
                    }
                    this.msg_buffer_callbacks = callbacks;

                } else {
                    // We haven't exceeded the throttle, send the message like 
                    // normal.
                    var data = {method: 'backbone', sync_data: attrs};
                    this.comm.send(data, callbacks);
                    this.pending_msgs++;
                }
            }
            // Since the comm is a one-way communication, assume the message 
            // arrived.  Don't call success since we don't have a model back from the server
            // this means we miss out on the 'sync' event.
            this._buffered_state_diff = {};
        },

        save_changes: function(callbacks) {
            // Push this model's state to the back-end
            //
            // This invokes a Backbone.Sync.
            this.save(this._buffered_state_diff, {patch: true, callbacks: callbacks});
        },

        _pack_models: function(value) {
            // Replace models with model ids recursively.
            if (value instanceof Backbone.Model) {
                return value.id;

            } else if ($.isArray(value)) {
                var packed = [];
                var that = this;
                _.each(value, function(sub_value, key) {
                    packed.push(that._pack_models(sub_value));
                });
                return packed;

            } else if (value instanceof Object) {
                var packed = {};
                var that = this;
                _.each(value, function(sub_value, key) {
                    packed[key] = that._pack_models(sub_value);
                });
                return packed;

            } else {
                return value;
            }
        },

        _unpack_models: function(value) {
            // Replace model ids with models recursively.
            if ($.isArray(value)) {
                var unpacked = [];
                var that = this;
                _.each(value, function(sub_value, key) {
                    unpacked.push(that._unpack_models(sub_value));
                });
                return unpacked;

            } else if (value instanceof Object) {
                var unpacked = {};
                var that = this;
                _.each(value, function(sub_value, key) {
                    unpacked[key] = that._unpack_models(sub_value);
                });
                return unpacked;

            } else {
                var model = this.widget_manager.get_model(value);
                if (model) {
                    return model;
                } else {
                    return value;
                }
            }
        },

    });
    WidgetManager.register_widget_model('WidgetModel', WidgetModel);


    var WidgetView = Backbone.View.extend({
        initialize: function(parameters) {
            // Public constructor.
            this.model.on('change',this.update,this);
            this.options = parameters.options;
            this.child_views = [];
            this.model.views.push(this);
        },

        update: function(){
            // Triggered on model change.
            //
            // Update view to be consistent with this.model
        },

        create_child_view: function(child_model, options) {
            // Create and return a child view.
            //
            // -given a model and (optionally) a view name if the view name is 
            // not given, it defaults to the model's default view attribute.
        
            // TODO: this is hacky, and makes the view depend on this cell attribute and widget manager behavior
            // it would be great to have the widget manager add the cell metadata
            // to the subview without having to add it here.
            var child_view = this.model.widget_manager.create_view(child_model, options || {}, this);
            this.child_views[child_model.id] = child_view;
            return child_view;
        },

        delete_child_view: function(child_model, options) {
            // Delete a child view that was previously created using create_child_view.
            var view = this.child_views[child_model.id];
            if (view !== undefined) {
                delete this.child_views[child_model.id];
                view.remove();
            }
        },

        do_diff: function(old_list, new_list, removed_callback, added_callback) {
            // Difference a changed list and call remove and add callbacks for 
            // each removed and added item in the new list.
            //
            // Parameters
            // ----------
            // old_list : array
            // new_list : array
            // removed_callback : Callback(item)
            //      Callback that is called for each item removed.
            // added_callback : Callback(item)
            //      Callback that is called for each item added.


            // removed items
            _.each(_.difference(old_list, new_list), function(item, index, list) {
                removed_callback(item);
            }, this);

            // added items
            _.each(_.difference(new_list, old_list), function(item, index, list) {
                added_callback(item);
            }, this);
        },

        callbacks: function(){
            // Create msg callbacks for a comm msg.
            return this.model.callbacks(this);
        },

        render: function(){
            // Render the view.
            //
            // By default, this is only called the first time the view is created
        },

        send: function (content) {
            // Send a custom msg associated with this view.
            this.model.send(content, this.callbacks());
        },

        touch: function () {
            this.model.save_changes(this.callbacks());
        },
    });


    var DOMWidgetView = WidgetView.extend({
        initialize: function (options) {
            // Public constructor

            // In the future we may want to make changes more granular 
            // (e.g., trigger on visible:change).
            this.model.on('change', this.update, this);
            this.model.on('msg:custom', this.on_msg, this);
            DOMWidgetView.__super__.initialize.apply(this, arguments);
        },
        
        on_msg: function(msg) {
            // Handle DOM specific msgs.
            switch(msg.msg_type) {
                case 'add_class':
                    this.add_class(msg.selector, msg.class_list);
                    break;
                case 'remove_class':
                    this.remove_class(msg.selector, msg.class_list);
                    break;
            }
        },

        add_class: function (selector, class_list) {
            // Add a DOM class to an element.
            this._get_selector_element(selector).addClass(class_list);
        },
        
        remove_class: function (selector, class_list) {
            // Remove a DOM class from an element.
            this._get_selector_element(selector).removeClass(class_list);
        },
    
        update: function () {
            // Update the contents of this view
            //
            // Called when the model is changed.  The model may have been 
            // changed by another view or by a state update from the back-end.
            //      The very first update seems to happen before the element is 
            // finished rendering so we use setTimeout to give the element time 
            // to render
            var e = this.$el;
            var visible = this.model.get('visible');
            setTimeout(function() {e.toggle(visible);},0);
     
            var css = this.model.get('_css');
            if (css === undefined) {return;}
            var that = this;
            _.each(css, function(css_traits, selector){
                // Apply the css traits to all elements that match the selector.
                var elements = that._get_selector_element(selector);
                if (elements.length > 0) {
                    _.each(css_traits, function(css_value, css_key){
                        elements.css(css_key, css_value);
                    });
                }
            });
        },

        _get_selector_element: function (selector) {
            // Get the elements via the css selector.

            // If the selector is blank, apply the style to the $el_to_style 
            // element.  If the $el_to_style element is not defined, use apply 
            // the style to the view's element.
            var elements;
            if (!selector) {
                if (this.$el_to_style === undefined) {
                    elements = this.$el;
                } else {
                    elements = this.$el_to_style;
                }
            } else {
                elements = this.$el.find(selector);
            }
            return elements;
        },
    });

    IPython.WidgetModel = WidgetModel;
    IPython.WidgetView = WidgetView;
    IPython.DOMWidgetView = DOMWidgetView;

    // Pass through WidgetManager namespace.
    return WidgetManager;
});
