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
        constructor: function (widget_manager, widget_id, comm) {
            this.widget_manager = widget_manager;
            this.pending_msgs = 0;
            this.msg_throttle = 3;
            this.msg_buffer = null;
            this.id = widget_id;

            if (comm !== undefined) {
                // Remember comm associated with the model.
                this.comm = comm;
                comm.model = this;

                // Hook comm messages up to model.
		var that = this;
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
	    // jng: widget manager should observe the comm_close event and delete views when triggered
	    this.trigger('comm:close');
            if (this._has_comm()) {
                delete this.comm.model; // Delete ref so GC will collect widget model.
                delete this.comm;
            }
            delete this.widget_id; // Delete id from model so widget manager cleans up.
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
		default:
		    // pass on to widget manager
		    this.widget_manager.handle_msg(msg, this);
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
                this.save();
            } finally {
                this.updating = false;
            }
        },


        _handle_status: function (msg, callbacks) {
            //execution_state : ('busy', 'idle', 'starting')
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

                        // Only decrease the pending message count if the buffer
                        // doesn't get flushed (sent).
                        --this.pending_msgs;
                    }
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

                        var data = {method: 'backbone', sync_method: method, sync_data: send_json};
                        this.comm.send(data, this.cell_callbacks());
                        this.pending_msgs++;
                    }
                }
            }
            
            // Since the comm is a one-way communication, assume the message 
            // arrived.
            return model_json;
        },

        // Build a callback dict.
        cell_callbacks: function (cell) {
            var callbacks = {};
            if (cell === undefined) {
		// Used the last modified view as the sender of the message.  This
		// will insure that any python code triggered by the sent message
		// can create and display widgets and output.
                if (this.last_modified_view !== undefined && 
                    this.last_modified_view.cell !== undefined) {
                    cell = this.last_modified_view.cell;
                } else {
		    cell = null;
		}
            }
            if (cell !== null) {
                
                // Try to get output handlers
                var handle_output = null;
                var handle_clear_output = null;
                if (cell.output_area !== undefined && cell.output_area !== null) {
                    handle_output = $.proxy(cell.output_area.handle_output, cell.output_area);
                    handle_clear_output = $.proxy(cell.output_area.handle_clear_output, cell.output_area);
                }

                // Create callback dict using what is known
                var that = this;
                callbacks = {
                    iopub : {
                        output : handle_output,
                        clear_output : handle_clear_output,

                        status : function (msg) {
                            that._handle_status(msg, that.cell_callbacks(cell));
                        },

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
	    this.cell = options.cell
        },

	update: function(){
	    // update thyself to be consistent with this.model
	},

	child_view: function(comm_id, view_name) {
	    var child_model = this.comm_manager.comms[comm_id].model;
	    var child_view = this.widget_manager.create_view(child_model, view_name, this.cell);
	    return child_view;
	},

	render: function(){
	    // render thyself
	},
        send: function (content) {
            this.model.send(content, this.model.cell_callbacks(this.cell));
        },

        touch: function () {
            this.model.last_modified_view = this;
            this.model.save(this.model.changedAttributes(), {patch: true});
        },
    });

    var WidgetView = BaseWidgetView.extend({
        initialize: function (options) {
            this.visible = true;
	    BaseWidgetView.prototype.initialize.apply(this, arguments);
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
	    // jng: hook into change:visible trigger
	    var visible = this.model.get('visible');
            if (visible !== undefined && this.visible !== visible) {
		this.visible = visible;
		this.$el.toggle(visible)
            }

            if (this.model.css !== undefined) {
                for (var selector in this.model.css) {
                    if (this.model.css.hasOwnProperty(selector)) {

                        // Apply the css traits to all elements that match the selector.
                        var elements = this._get_selector_element(selector);
                        if (elements.length > 0) {
                            var css_traits = this.model.css[selector];    
                            for (var css_key in css_traits) {
                                if (css_traits.hasOwnProperty(css_key)) {
                                    elements.css(css_key, css_traits[css_key]);
                                }
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
            var elements = this.$el.find(selector);
            if (selector === undefined || selector === null || selector === '') {
                if (this.$el_to_style === undefined) {
                    elements = this.$el;
                } else {
                    elements = this.$el_to_style;
                }
            }
            return elements;
        },
    });

    IPython.WidgetModel = WidgetModel;
    IPython.WidgetView = WidgetView;

    return widget_manager;
});
