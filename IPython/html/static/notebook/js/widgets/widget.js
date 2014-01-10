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

define(["notebook/js/widgetmanager",
        "underscore",
        "backbone"], 
function(widget_manager, underscore, backbone){

    var WidgetModel = Backbone.Model.extend({
        constructor: function (widget_manager, model_id, comm) {
            // Construcctor
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
            this.pending_msgs = 0;
            this.msg_throttle = 2;
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
                var data = {method: 'custom', custom_content: content};
                this.comm.send(data, callbacks);
            }
        },

        _handle_comm_closed: function (msg) {
            // Handle when a widget is closed.
            this.trigger('comm:close');
            delete this.comm.model; // Delete ref so GC will collect widget model.
            delete this.comm;
            delete this.model_id; // Delete id from model so widget manager cleans up.
            // TODO: Handle deletion, like this.destroy(), and delete views, etc.
        },

        _handle_comm_msg: function (msg) {
            // Handle incoming comm msg.
            var method = msg.content.data.method;
            switch (method) {
                case 'update':
                    this.apply_update(msg.content.data.state);
                    break;
                case 'custom':
                    this.trigger('msg:custom', msg.content.data.custom_content);
                    break;
                case 'display':
                    this.widget_manager.display_view(msg.parent_header.msg_id, this);
                    break;
            }
        },

        apply_update: function (state) {
            // Handle when a widget is updated via the python side.
            for (var key in state) {
                if (state.hasOwnProperty(key)) {
                    var value = state[key];
                    this.key_value_lock = [key, value];
                    try {
                        this.set(key, this._unpack_models(value));
                    } finally {
                        this.key_value_lock = null;
                    }
                }
            }
            //TODO: are there callbacks that make sense in this case?  If so, attach them here as an option
            this.save();
        },

        _handle_status: function (msg, callbacks) {
            // Handle status msgs.

            // execution_state : ('busy', 'idle', 'starting')
            if (this.comm !== undefined) {
                if (msg.content.execution_state ==='idle') {
                    // Send buffer if this message caused another message to be
                    // throttled.
                    if (this.msg_buffer !== null &&
                        this.msg_throttle === this.pending_msgs) {
                        var data = {method: 'backbone', sync_method: 'update', sync_data: this.msg_buffer};
                        this.comm.send(data, callbacks);  
                        this.msg_buffer = null;
                    } else {
                        --this.pending_msgs;
                    }
                }
            }
        },

        _handle_sync: function (method, options) {
            // Custom syncronization logic.
            var model_json = this.toJSON();
            var attr;

            // Only send updated state if the state hasn't been changed 
            // during an update.
            if (this.comm !== undefined) {    
                if (this.pending_msgs >= this.msg_throttle) {
                    // The throttle has been exceeded, buffer the current msg so
                    // it can be sent once the kernel has finished processing 
                    // some of the existing messages.
                    if (this.msg_buffer === null) {
                        this.msg_buffer = $.extend({}, model_json); // Copy
                    }
                    for (attr in options.attrs) {
                        var value = this._pack_models(options.attrs[attr]);
                        if (this.key_value_lock === null || attr !== this.key_value_lock[0] || value !== this.key_value_lock[1]) {
                            this.msg_buffer[attr] = value;
                        }
                    }

                } else {
                    // We haven't exceeded the throttle, send the message like 
                    // normal.  If this is a patch operation, just send the 
                    // changes.
                    var send_json = model_json;
                    send_json = {};
                    for (attr in options.attrs) {
                        var value = this._pack_models(options.attrs[attr]);
                        if (this.key_value_lock === null || attr !== this.key_value_lock[0] || value !== this.key_value_lock[1]) {
                            send_json[attr] = value;
                        }
                    }
                    
                    var is_empty = true;
                    for (var prop in send_json) if (send_json.hasOwnProperty(prop)) is_empty = false;
                    if (!is_empty) {
                        ++this.pending_msgs;
                        var data = {method: 'backbone', sync_data: send_json};
                        this.comm.send(data, options.callbacks);
                    }
                }
            }
            
            // Since the comm is a one-way communication, assume the message 
            // arrived.
            return model_json;
        },

        push: function(callbacks) {
			// Push this model's state to the back-end
			//
			// This invokes a Backbone.Sync.
            this.save(this.changedAttributes(), {patch: true, callbacks: callbacks});
        },

        _pack_models: function(value) {
            // Replace models with model ids recursively.
            if (value instanceof Backbone.Model) {
                return value.id;
            } else if (value instanceof Object) {
                var packed = {};
                for (var key in value) {
                    packed[key] = this._pack_models(value[key]);
                }
                return packed;
            } else {
                return value;
            }
        },

        _unpack_models: function(value) {
            // Replace model ids with models recursively.
            if (value instanceof Object) {
                var unpacked = {};
                for (var key in value) {
                    unpacked[key] = this._unpack_models(value[key]);
                }
                return unpacked;
            } else {
                var model = this.widget_manager.get_model(value);
                if (model !== null) {
                    return model;
                } else {
                    return value;
                }
            }
        },

    });
    widget_manager.register_widget_model('WidgetModel', WidgetModel);


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
	        options = options || {};
            options.cell = this.options.cell;
            var child_view = this.model.widget_manager.create_view(child_model, options);
            this.child_views[child_model.id] = child_view;
            return child_view;
        },

        delete_child_view: function(child_model, options) {
            // Delete a child view that was previously created using create_child_view.
            var view = this.child_views[child_model.id];
            delete this.child_views[child_model.id];
            view.remove();
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
            return this.model.widget_manager.callbacks(this);
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
            this.model.push(this.callbacks());
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
            setTimeout(function() {e.toggle(visible)},0);
     
            var css = this.model.get('_css');
            if (css === undefined) {return;}
            for (var selector in css) {
                if (css.hasOwnProperty(selector)) {
                    // Apply the css traits to all elements that match the selector.
                    var elements = this._get_selector_element(selector);
                    if (elements.length > 0) {
                        var css_traits = css[selector];    
                        for (var css_key in css_traits) {
                            if (css_traits.hasOwnProperty(css_key)) {
                                elements.css(css_key, css_traits[css_key]);
                            }
                        }
                    }
                }
            }
        },

        _get_selector_element: function (selector) {
            // Get the elements via the css selector.  

            // If the selector is blank, apply the style to the $el_to_style 
            // element.  If the $el_to_style element is not defined, use apply 
            // the style to the view's element.
            var elements;
            if (selector === undefined || selector === null || selector === '') {
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

    // Pass through widget_manager instance (probably not a good practice).
    return widget_manager;
});
