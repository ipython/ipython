// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define(["widgets/js/manager",
        "underscore",
        "backbone",
        "jquery",
        "base/js/utils",
        "base/js/namespace",
], function(widgetmanager, _, Backbone, $, utils, IPython){

    var WidgetModel = Backbone.Model.extend({
        constructor: function (widget_manager, model_id, comm) {
            /**
             * Constructor
             *
             * Creates a WidgetModel instance.
             *
             * Parameters
             * ----------
             * widget_manager : WidgetManager instance
             * model_id : string
             *      An ID unique to this model.
             * comm : Comm instance (optional)
             */
            this.widget_manager = widget_manager;
            this.state_change = Promise.resolve();
            this._buffered_state_diff = {};
            this.pending_msgs = 0;
            this.msg_buffer = null;
            this.state_lock = null;
            this.id = model_id;
            this.views = {};

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
            /**
             * Send a custom msg over the comm.
             */
            if (this.comm !== undefined) {
                var data = {method: 'custom', content: content};
                this.comm.send(data, callbacks);
                this.pending_msgs++;
            }
        },

        _handle_comm_closed: function (msg) {
            /**
             * Handle when a widget is closed.
             */
            this.trigger('comm:close');
            this.stopListening();
            this.trigger('destroy', this);
            delete this.comm.model; // Delete ref so GC will collect widget model.
            delete this.comm;
            delete this.model_id; // Delete id from model so widget manager cleans up.
            for (var id in this.views) {
                if (this.views.hasOwnProperty(id)) {
                    this.views[id].remove();
                }
            }
        },

        _handle_comm_msg: function (msg) {
            /**
             * Handle incoming comm msg.
             */
            var method = msg.content.data.method;
            var that = this;
            switch (method) {
                case 'update':
                    this.state_change = this.state_change.then(function() {
                        return that.set_state(msg.content.data.state);
                    }).catch(utils.reject("Couldn't process update msg for model id '" + String(that.id) + "'", true));
                    break;
                case 'custom':
                    this.trigger('msg:custom', msg.content.data.content);
                    break;
                case 'display':
                    this.widget_manager.display_view(msg, this);
                    break;
            }
        },

        set_state: function (state) {
            var that = this;
            // Handle when a widget is updated via the python side.
            return this._unpack_models(state).then(function(state) {
                that.state_lock = state;
                try {
                    WidgetModel.__super__.set.call(that, state);
                } finally {
                    that.state_lock = null;
                }
            }).catch(utils.reject("Couldn't set model state", true));
        },

        _handle_status: function (msg, callbacks) {
            /**
             * Handle status msgs.
             *
             * execution_state : ('busy', 'idle', 'starting')
             */
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
            /**
             * Create msg callbacks for a comm msg.
             */
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
            /**
             * Set a value.
             */
            var return_value = WidgetModel.__super__.set.apply(this, arguments);

            // Backbone only remembers the diff of the most recent set()
            // operation.  Calling set multiple times in a row results in a 
            // loss of diff information.  Here we keep our own running diff.
            this._buffered_state_diff = $.extend(this._buffered_state_diff, this.changedAttributes() || {});
            return return_value;
        },

        sync: function (method, model, options) {
            /**
             * Handle sync to the back-end.  Called when a model.save() is called.
             *
             * Make sure a comm exists.
             */
            var error = options.error || function() {
                console.error('Backbone sync error:', arguments);
            };
            if (this.comm === undefined) {
                error();
                return false;
            }

            // Delete any key value pairs that the back-end already knows about.
            var attrs = (method === 'patch') ? options.attrs : model.toJSON(options);
            if (this.state_lock !== null) {
                var keys = Object.keys(this.state_lock);
                for (var i=0; i<keys.length; i++) {
                    var key = keys[i];
                    if (attrs[key] === this.state_lock[key]) {
                        delete attrs[key];
                    }
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
            /**
             * Push this model's state to the back-end
             *
             * This invokes a Backbone.Sync.
             */
            this.save(this._buffered_state_diff, {patch: true, callbacks: callbacks});
        },

        _pack_models: function(value) {
            /**
             * Replace models with model ids recursively.
             */
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
            } else if (value instanceof Date || value instanceof String) {
                return value;
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
            /**
             * Replace model ids with models recursively.
             */
            var that = this;
            var unpacked;
            if ($.isArray(value)) {
                unpacked = [];
                _.each(value, function(sub_value, key) {
                    unpacked.push(that._unpack_models(sub_value));
                });
                return Promise.all(unpacked);
            } else if (value instanceof Object) {
                unpacked = {};
                _.each(value, function(sub_value, key) {
                    unpacked[key] = that._unpack_models(sub_value);
                });
                return utils.resolve_promises_dict(unpacked);
            } else if (typeof value === 'string' && value.slice(0,10) === "IPY_MODEL_") {
                // get_model returns a promise already
                return this.widget_manager.get_model(value.slice(10, value.length));
            } else {
                return Promise.resolve(value);
            }
        },

        on_some_change: function(keys, callback, context) {
            /**
             * on_some_change(["key1", "key2"], foo, context) differs from
             * on("change:key1 change:key2", foo, context).
             * If the widget attributes key1 and key2 are both modified, 
             * the second form will result in foo being called twice
             * while the first will call foo only once.
             */
            this.on('change', function() {
                if (keys.some(this.hasChanged, this)) {
                    callback.apply(context);
                }
            }, this);

       },
    });
    widgetmanager.WidgetManager.register_widget_model('WidgetModel', WidgetModel);


    var WidgetView = Backbone.View.extend({
        initialize: function(parameters) {
            /**
             * Public constructor.
             */
            this.model.on('change',this.update,this);
            this.options = parameters.options;
            this.id = this.id || utils.uuid();
            this.model.views[this.id] = this;
            this.on('displayed', function() { 
                this.is_displayed = true; 
            }, this);
        },

        update: function(){
            /**
             * Triggered on model change.
             *
             * Update view to be consistent with this.model
             */
        },

        create_child_view: function(child_model, options) {
            /**
             * Create and promise that resolves to a child view of a given model
             */
            var that = this;
            options = $.extend({ parent: this }, options || {});
            return this.model.widget_manager.create_view(child_model, options).catch(utils.reject("Couldn't create child view"), true);
        },

        callbacks: function(){
            /**
             * Create msg callbacks for a comm msg.
             */
            return this.model.callbacks(this);
        },

        render: function(){
            /**
             * Render the view.
             *
             * By default, this is only called the first time the view is created
             */
        },

        show: function(){
            /**
             * Show the widget-area
             */
            if (this.options && this.options.cell &&
                this.options.cell.widget_area !== undefined) {
                this.options.cell.widget_area.show();
            }
        },

        send: function (content) {
            /**
             * Send a custom msg associated with this view.
             */
            this.model.send(content, this.callbacks());
        },

        touch: function () {
            this.model.save_changes(this.callbacks());
        },

        after_displayed: function (callback, context) {
            /**
             * Calls the callback right away is the view is already displayed
             * otherwise, register the callback to the 'displayed' event.
             */
            if (this.is_displayed) {
                callback.apply(context);
            } else {
                this.on('displayed', callback, context);
            }
        }
    });


    var DOMWidgetView = WidgetView.extend({
        initialize: function (parameters) {
            /**
             * Public constructor
             */
            DOMWidgetView.__super__.initialize.apply(this, [parameters]);
            this.on('displayed', this.show, this);
            this.model.on('change:visible', this.update_visible, this);
            this.model.on('change:_css', this.update_css, this);

            this.model.on('change:_dom_classes', function(model, new_classes) {
                var old_classes = model.previous('_dom_classes');
                this.update_classes(old_classes, new_classes);
            }, this);

            this.model.on('change:color', function (model, value) { 
                this.update_attr('color', value); }, this);

            this.model.on('change:background_color', function (model, value) { 
                this.update_attr('background', value); }, this);

            this.model.on('change:width', function (model, value) { 
                this.update_attr('width', value); }, this);

            this.model.on('change:height', function (model, value) { 
                this.update_attr('height', value); }, this);

            this.model.on('change:border_color', function (model, value) { 
                this.update_attr('border-color', value); }, this);

            this.model.on('change:border_width', function (model, value) { 
                this.update_attr('border-width', value); }, this);

            this.model.on('change:border_style', function (model, value) { 
                this.update_attr('border-style', value); }, this);

            this.model.on('change:font_style', function (model, value) { 
                this.update_attr('font-style', value); }, this);

            this.model.on('change:font_weight', function (model, value) { 
                this.update_attr('font-weight', value); }, this);

            this.model.on('change:font_size', function (model, value) { 
                this.update_attr('font-size', this._default_px(value)); }, this);

            this.model.on('change:font_family', function (model, value) { 
                this.update_attr('font-family', value); }, this);

            this.model.on('change:padding', function (model, value) { 
                this.update_attr('padding', value); }, this);

            this.model.on('change:margin', function (model, value) { 
                this.update_attr('margin', this._default_px(value)); }, this);

            this.model.on('change:border_radius', function (model, value) { 
                this.update_attr('border-radius', this._default_px(value)); }, this);

            this.after_displayed(function() {
                this.update_visible(this.model, this.model.get("visible"));
                this.update_classes([], this.model.get('_dom_classes'));
                
                this.update_attr('color', this.model.get('color'));
                this.update_attr('background', this.model.get('background_color'));
                this.update_attr('width', this.model.get('width'));
                this.update_attr('height', this.model.get('height'));
                this.update_attr('border-color', this.model.get('border_color'));
                this.update_attr('border-width', this.model.get('border_width'));
                this.update_attr('border-style', this.model.get('border_style'));
                this.update_attr('font-style', this.model.get('font_style'));
                this.update_attr('font-weight', this.model.get('font_weight'));
                this.update_attr('font-size', this.model.get('font_size'));
                this.update_attr('font-family', this.model.get('font_family'));
                this.update_attr('padding', this.model.get('padding'));
                this.update_attr('margin', this.model.get('margin'));
                this.update_attr('border-radius', this.model.get('border_radius'));

                this.update_css(this.model, this.model.get("_css"));
            }, this);
        },

        _default_px: function(value) {
            /**
             * Makes browser interpret a numerical string as a pixel value.
             */
            if (/^\d+\.?(\d+)?$/.test(value.trim())) {
                return value.trim() + 'px';
            }
            return value;
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            this.$el.css(name, value);
        },

        update_visible: function(model, value) {
            /**
             * Update visibility
             */
            this.$el.toggle(value);
         },

        update_css: function (model, css) {
            /**
             * Update the css styling of this view.
             */
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

        update_classes: function (old_classes, new_classes, $el) {
            /**
             * Update the DOM classes applied to an element, default to this.$el.
             */
            if ($el===undefined) {
                $el = this.$el;
            }
            _.difference(old_classes, new_classes).map(function(c) {$el.removeClass(c);})
            _.difference(new_classes, old_classes).map(function(c) {$el.addClass(c);})
        },

        update_mapped_classes: function(class_map, trait_name, previous_trait_value, $el) {
            /**
             * Update the DOM classes applied to the widget based on a single
             * trait's value.
             *
             * Given a trait value classes map, this function automatically
             * handles applying the appropriate classes to the widget element
             * and removing classes that are no longer valid.
             *
             * Parameters
             * ----------
             * class_map: dictionary
             *  Dictionary of trait values to class lists.
             *  Example:
             *      {
             *          success: ['alert', 'alert-success'],
             *          info: ['alert', 'alert-info'],
             *          warning: ['alert', 'alert-warning'],
             *          danger: ['alert', 'alert-danger']
             *      };
             * trait_name: string
             *  Name of the trait to check the value of.
             * previous_trait_value: optional string, default ''
             *  Last trait value
             * $el: optional jQuery element handle, defaults to this.$el
             *  Element that the classes are applied to.
             */
            var key = previous_trait_value;
            if (key === undefined) {
                key = this.model.previous(trait_name);
            }
            var old_classes = class_map[key] ? class_map[key] : [];
            key = this.model.get(trait_name);
            var new_classes = class_map[key] ? class_map[key] : [];

            this.update_classes(old_classes, new_classes, $el || this.$el);
        },
        
        _get_selector_element: function (selector) {
            /**
             * Get the elements via the css selector.
             */
            var elements;
            if (!selector) {
                elements = this.$el;
            } else {
                elements = this.$el.find(selector).addBack(selector);
            }
            return elements;
        },

        typeset: function(element, text){
            utils.typeset.apply(null, arguments);
        },
    });


    var ViewList = function(create_view, remove_view, context) {
        /**
         * - create_view and remove_view are default functions called when adding or removing views
         * - create_view takes a model and returns a view or a promise for a view for that model
         * - remove_view takes a view and destroys it (including calling `view.remove()`)
         * - each time the update() function is called with a new list, the create and remove
         *   callbacks will be called in an order so that if you append the views created in the
         *   create callback and remove the views in the remove callback, you will duplicate 
         *   the order of the list.
         * - the remove callback defaults to just removing the view (e.g., pass in null for the second parameter)
         * - the context defaults to the created ViewList.  If you pass another context, the create and remove
         *   will be called in that context.
         */

        this.initialize.apply(this, arguments);
    };

    _.extend(ViewList.prototype, {
        initialize: function(create_view, remove_view, context) {
            this.state_change = Promise.resolve();
            this._handler_context = context || this;
            this._models = [];
            this.views = [];
            this._create_view = create_view;
            this._remove_view = remove_view || function(view) {view.remove();};
        },

        update: function(new_models, create_view, remove_view, context) {
            /**
             * the create_view, remove_view, and context arguments override the defaults
             * specified when the list is created.
             * returns a promise that resolves after this update is done
             */
            var remove = remove_view || this._remove_view;
            var create = create_view || this._create_view;
            if (create === undefined || remove === undefined){
                console.error("Must define a create a remove function");
            }
            var context = context || this._handler_context;
            var added_views = [];
            var that = this;
            this.state_change = this.state_change.then(function() {
                var i;
                 // first, skip past the beginning of the lists if they are identical
                for (i = 0; i < new_models.length; i++) {
                    if (i >= that._models.length || new_models[i] !== that._models[i]) {
                        break;
                    }
                }
                var first_removed = i;
                // Remove the non-matching items from the old list.
                for (var j = first_removed; j < that._models.length; j++) {
                    remove.call(context, that.views[j]);
                }

                // Add the rest of the new list items.
                for (; i < new_models.length; i++) {
                    added_views.push(create.call(context, new_models[i]));
                }
                // make a copy of the input array
                that._models = new_models.slice();
                return Promise.all(added_views).then(function(added) {
                    Array.prototype.splice.apply(that.views, [first_removed, that.views.length].concat(added));
                    return that.views;
                });
            });
            return this.state_change;
        },

        remove: function() {
            /**
             * removes every view in the list; convenience function for `.update([])`
             * that should be faster
             * returns a promise that resolves after this removal is done
             */
            var that = this;
            this.state_change = this.state_change.then(function() {
                for (var i = 0; i < that.views.length; i++) {
                    that._remove_view.call(that._handler_context, that.views[i]);
                }
                that._models = [];
                that.views = [];
            });
            return this.state_change;
        },
    });

    var widget = {
        'WidgetModel': WidgetModel,
        'WidgetView': WidgetView,
        'DOMWidgetView': DOMWidgetView,
        'ViewList': ViewList,
    };

    // For backwards compatability.
    $.extend(IPython, widget);

    return widget;
});
