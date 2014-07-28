// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define(["widgets/js/manager",
        "underscore",
        "backbone", 
        "jquery",   
        "base/js/namespace",
], function(widgetmanager, _, Backbone, $, IPython){

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
            var that = this;
            var packed;
            if (value instanceof Backbone.Model) {
                return "IPY_MODEL_" + value.id;

            } else if ($.isArray(value)) {
                packed = [];
                _.each(value, function(sub_value, key) {
                    packed.push(that._pack_models(sub_value));
                });
                return packed;

            } else if (value instanceof Object) {
                packed = {};
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
            var that = this;
            var unpacked;
            if ($.isArray(value)) {
                unpacked = [];
                _.each(value, function(sub_value, key) {
                    unpacked.push(that._unpack_models(sub_value));
                });
                return unpacked;

            } else if (value instanceof Object) {
                unpacked = {};
                _.each(value, function(sub_value, key) {
                    unpacked[key] = that._unpack_models(sub_value);
                });
                return unpacked;

            } else if (typeof value === 'string' && value.slice(0,10) === "IPY_MODEL_") {
		var model = this.widget_manager.get_model(value.slice(10, value.length));
		if (model) {
		    return model;
		} else {
		    return value;
		}
            } else {
                    return value;
            }
        },

    });
    widgetmanager.WidgetManager.register_widget_model('WidgetModel', WidgetModel);


    var WidgetView = Backbone.View.extend({
        initialize: function(parameters) {
            // Public constructor.
            this.model.on('change',this.update,this);
            this.options = parameters.options;
            this.child_model_views = {};
            this.child_views = {};
            this.model.views.push(this);
            this.id = this.id || IPython.utils.uuid();
            this.on('displayed', function() { 
                this.is_displayed = true; 
            }, this);
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
            options = $.extend({ parent: this }, options || {});
            var child_view = this.model.widget_manager.create_view(child_model, options, this);
            
            // Associate the view id with the model id.
            if (this.child_model_views[child_model.id] === undefined) {
                this.child_model_views[child_model.id] = [];
            }
            this.child_model_views[child_model.id].push(child_view.id);

            // Remember the view by id.
            this.child_views[child_view.id] = child_view;
            return child_view;
        },

        pop_child_view: function(child_model) {
            // Delete a child view that was previously created using create_child_view.
            var view_ids = this.child_model_views[child_model.id];
            if (view_ids !== undefined) {

                // Only delete the first view in the list.
                var view_id = view_ids[0];
                var view = this.child_views[view_id];
                delete this.child_views[view_id];
                view_ids.splice(0,1);
                child_model.views.pop(view);
            
                // Remove the view list specific to this model if it is empty.
                if (view_ids.length === 0) {
                    delete this.child_model_views[child_model.id];
                }
                return view;
            }
            return null;
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

            // Walk the lists until an unequal entry is found.
            var i;
            for (i = 0; i < new_list.length; i++) {
                if (i >= old_list.length || new_list[i] !== old_list[i]) {
                    break;
                }
            }

            // Remove the non-matching items from the old list.
            for (var j = i; j < old_list.length; j++) {
                removed_callback(old_list[j]);
            }

            // Add the rest of the new list items.
            for (; i < new_list.length; i++) {
                added_callback(new_list[i]);
            }
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

        show: function(){
            // Show the widget-area
            if (this.options && this.options.cell &&
                this.options.cell.widget_area !== undefined) {
                this.options.cell.widget_area.show();
            }
        },

        send: function (content) {
            // Send a custom msg associated with this view.
            this.model.send(content, this.callbacks());
        },

        touch: function () {
            this.model.save_changes(this.callbacks());
        },

        after_displayed: function (callback, context) {
            // Calls the callback right away is the view is already displayed
            // otherwise, register the callback to the 'displayed' event.
            if (this.is_displayed) {
                callback.apply(context);
            } else {
                this.on('displayed', callback, context);
            }
        },
    });


    var DOMWidgetView = WidgetView.extend({
        initialize: function (parameters) {
            // Public constructor
            DOMWidgetView.__super__.initialize.apply(this, [parameters]);
            this.on('displayed', this.show, this);
            this.after_displayed(function() {
                this.update_visible(this.model, this.model.get("visible"));
                this.update_css(this.model, this.model.get("_css"));
            }, this);
            this.model.on('msg:custom', this.on_msg, this);
            this.model.on('change:visible', this.update_visible, this);
            this.model.on('change:_css', this.update_css, this);
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

        update_visible: function(model, value) {
            // Update visibility
            this.$el.toggle(value);
         },

        update_css: function (model, css) {
            // Update the css styling of this view.
            var e = this.$el;
            if (css === undefined) {return;}
            for (var i = 0; i < css.length; i++) {
                // Apply the css traits to all elements that match the selector.
                var selector = css[i][0];
                var elements = this._get_selector_element(selector);
                if (elements.length > 0) {
                    var trait_key = css[i][1];
                    var trait_value = css[i][2];
                    elements.css(trait_key ,trait_value);
                }
            }
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

    var widget = {
        'WidgetModel': WidgetModel,
        'WidgetView': WidgetView,
        'DOMWidgetView': DOMWidgetView,
    };

    // For backwards compatability.
    $.extend(IPython, widget);

    return widget;
});
