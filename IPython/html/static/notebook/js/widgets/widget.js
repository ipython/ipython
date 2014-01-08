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
    
    //--------------------------------------------------------------------
    // WidgetModel class
    //--------------------------------------------------------------------
    var WidgetModel = Backbone.Model.extend({
        constructor: function (widget_manager, model_id, comm) {
            this.widget_manager = widget_manager;
            this.pending_msgs = 0;
            this.msg_throttle = 3;
            this.msg_buffer = null;
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
            if (this.comm !== undefined) {
                var data = {method: 'custom', custom_content: content};
                this.comm.send(data, callbacks);
            }
        },

        // Handle when a widget is closed.
        _handle_comm_closed: function (msg) {
            this.trigger('comm:close');
            delete this.comm.model; // Delete ref so GC will collect widget model.
            delete this.comm;
            delete this.model_id; // Delete id from model so widget manager cleans up.
            // TODO: Handle deletion, like this.destroy(), and delete views, etc.
        },


        // Handle incoming comm msg.
        _handle_comm_msg: function (msg) {
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


        // Handle when a widget is updated via the python side.
        apply_update: function (state) {
            this.updating = true;
            try {
                for (var key in state) {
                    if (state.hasOwnProperty(key)) {
                            this.set(key, state[key]);
                    }
                }
                //TODO: are there callbacks that make sense in this case?  If so, attach them here as an option
                this.save();
            } finally {
                this.updating = false;
            }
        },


        _handle_status: function (msg, callbacks) {
            //execution_state : ('busy', 'idle', 'starting')
            if (this.comm !== undefined && msg.content.execution_state ==='idle') {
                // Send buffer if this message caused another message to be
                // throttled.
                if (this.msg_buffer !== null &&
                    this.msg_throttle === this.pending_msgs) {
                    var data = {method: 'backbone', sync_method: 'update', sync_data: this.msg_buffer};
                    this.comm.send(data, callbacks);   
                    this.msg_buffer = null;
                } else {
                    // Only decrease the pending message count if the buffer
                    // doesn't get flushed (sent).
                    --this.pending_msgs;
                }
            }
        },


        // Custom syncronization logic.
        _handle_sync: function (method, options) {
            var model_json = this.toJSON();
            var attr;

            // Only send updated state if the state hasn't been changed 
            // during an update.
            if (this.comm !== undefined) {
                if (!this.updating) {
                    if (this.pending_msgs >= this.msg_throttle) {
                        // The throttle has been exceeded, buffer the current msg so
                        // it can be sent once the kernel has finished processing 
                        // some of the existing messages.
                        if (method=='patch') {
                            if (this.msg_buffer === null) {
                                this.msg_buffer = $.extend({}, model_json); // Copy
                            }
                            for (attr in options.attrs) {
                                this.msg_buffer[attr] = options.attrs[attr];
                            }
                        } else {
                            this.msg_buffer = $.extend({}, model_json); // Copy
                        }

                    } else {
                        // We haven't exceeded the throttle, send the message like 
                        // normal.  If this is a patch operation, just send the 
                        // changes.
                        var send_json = model_json;
                        if (method =='patch') {
                            send_json = {};
                            for (attr in options.attrs) {
                                send_json[attr] = options.attrs[attr];
                            }
                        }

                        var data = {method: 'backbone', sync_data: send_json};
                        this.comm.send(data, options.callbacks);
                        this.pending_msgs++;
                    }
                }
            }
            
            // Since the comm is a one-way communication, assume the message 
            // arrived.
            return model_json;
        },

    });


    //--------------------------------------------------------------------
    // WidgetView class
    //--------------------------------------------------------------------
    var BaseWidgetView = Backbone.View.extend({
        initialize: function(options) {
            this.model.on('change',this.update,this);
            this.widget_manager = options.widget_manager;
            this.comm_manager = options.widget_manager.comm_manager;
            this.options = options.options;
            this.child_views = [];
            this.model.views.push(this);
        },

        update: function(){
            // update view to be consistent with this.model
            // triggered on model change
        },

        child_view: function(model_id, view_name, options) {
            // create and return a child view, given a model id for a model and (optionally) a view name
            // if the view name is not given, it defaults to the model's default view attribute
            var child_model = this.widget_manager.get_model(model_id);
            var child_view = this.widget_manager.create_view(child_model, view_name, options);
            this.child_views[model_id] = child_view;
            return child_view;
        },
        
        update_child_views: function(old_list, new_list) {
            // this function takes an old list and new list of model ids
            // views in child_views that correspond to deleted ids are deleted
            // views corresponding to added ids are added child_views
        
            // delete old views
            _.each(_.difference(old_list, new_list), function(element, index, list) {
                var view = this.child_views[element];
                delete this.child_views[element];
                view.remove();
            }, this);
            
            // add new views
            _.each(_.difference(new_list, old_list), function(element, index, list) {
                // this function adds the view to the child_views dictionary
                this.child_view(element);
            }, this);
        },

        callbacks: function(){
            return this.widget_manager.callbacks(this);
        },

        render: function(){
            // render the view.  By default, this is only called the first time the view is created
        },
        send: function (content) {
            this.model.send(content, this.callbacks());
        },

        touch: function () {
            this.model.save(this.model.changedAttributes(), {patch: true, callbacks: this.callbacks()});
        },

    });

    var WidgetView = BaseWidgetView.extend({
        initialize: function (options) {
            // TODO: make changes more granular (e.g., trigger on visible:change)
            this.model.on('change', this.update, this);
            this.model.on('msg:custom', this.on_msg, this);
            BaseWidgetView.prototype.initialize.apply(this, arguments);
        },
        
        on_msg: function(msg) {
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
            var elements = this._get_selector_element(selector);
            if (elements.length > 0) {
                elements.addClass(class_list);
            }
        },
        
        remove_class: function (selector, class_list) {
            var elements = this._get_selector_element(selector);
            if (elements.length > 0) {
                elements.removeClass(class_list);
            }
        },
    
        update: function () {
            // the very first update seems to happen before the element is finished rendering
            // so we use setTimeout to give the element time to render
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
            // Get the elements via the css selector.  If the selector is
            // blank, apply the style to the $el_to_style element.  If
            // the $el_to_style element is not defined, use apply the 
            // style to the view's element.
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
    IPython.BaseWidgetView = BaseWidgetView;

    return widget_manager;
});
