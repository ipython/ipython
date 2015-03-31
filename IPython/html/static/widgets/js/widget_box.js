// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jqueryui",
    "underscore",
    "base/js/utils",
    "bootstrap",
], function(widget, $, _, utils){
    "use strict";
    var unpack_models = function unpack_models(value, model) {
        /**
         * Replace model ids with models recursively.
         */
        var unpacked;
        if ($.isArray(value)) {
            unpacked = [];
            _.each(value, function(sub_value, key) {
                unpacked.push(unpack_models(sub_value, model));
            });
            return Promise.all(unpacked);
        } else if (value instanceof Object) {
            unpacked = {};
            _.each(value, function(sub_value, key) {
                unpacked[key] = unpack_models(sub_value, model);
            });
            return utils.resolve_promises_dict(unpacked);
        } else if (typeof value === 'string' && value.slice(0,10) === "IPY_MODEL_") {
            // get_model returns a promise already
            return model.widget_manager.get_model(value.slice(10, value.length));
        } else {
            return Promise.resolve(value);
        }
    };

    var BoxModel = widget.WidgetModel.extend({}, {
        serializers: _.extend({
            children: {deserialize: unpack_models}
        }, widget.WidgetModel.serializers)
    });

    var BoxView = widget.DOMWidgetView.extend({
        initialize: function(){
            /**
             * Public constructor
             */
            BoxView.__super__.initialize.apply(this, arguments);
            this.children_views = new widget.ViewList(this.add_child_model, null, this);
            this.listenTo(this.model, 'change:children', function(model, value) {
                this.children_views.update(value);
            }, this);
            this.listenTo(this.model, 'change:overflow_x', function(model, value) {
                this.update_overflow_x();
            }, this);
            this.listenTo(this.model, 'change:overflow_y', function(model, value) {
                this.update_overflow_y();
            }, this);
            this.listenTo(this.model, 'change:box_style', function(model, value) {
                this.update_box_style();
            }, this);
        },

        update_attr: function(name, value) {
            /**
             * Set a css attr of the widget view.
             */
            this.$box.css(name, value);
        },

        render: function(){
            /**
             * Called when view is rendered.
             */
            this.$box = this.$el;
            this.$box.addClass('widget-box');
            this.children_views.update(this.model.get('children'));
            this.update_overflow_x();
            this.update_overflow_y();
            this.update_box_style('');
        },

        update_overflow_x: function() {
            /**
             * Called when the x-axis overflow setting is changed.
             */
            this.$box.css('overflow-x', this.model.get('overflow_x'));
        },

        update_overflow_y: function() {
            /**
             * Called when the y-axis overflow setting is changed.
             */
            this.$box.css('overflow-y', this.model.get('overflow_y'));
        },

        update_box_style: function(previous_trait_value) {
            var class_map = {
                success: ['alert', 'alert-success'],
                info: ['alert', 'alert-info'],
                warning: ['alert', 'alert-warning'],
                danger: ['alert', 'alert-danger']
            };
            this.update_mapped_classes(class_map, 'box_style', previous_trait_value, this.$box);
        },
        
        add_child_model: function(model) {
            /**
             * Called when a model is added to the children list.
             */
            var that = this;
            var dummy = $('<div/>');
            that.$box.append(dummy);
            return this.create_child_view(model).then(function(view) {
                dummy.replaceWith(view.el);

                // Trigger the displayed event of the child view.
                that.after_displayed(function() {
                    view.trigger('displayed');
                });
                return view;
            }).catch(utils.reject("Couldn't add child view to box", true));
        },
        
        remove: function() {
            /**
             * We remove this widget before removing the children as an optimization
             * we want to remove the entire container from the DOM first before
             * removing each individual child separately.
             */
            BoxView.__super__.remove.apply(this, arguments);
            this.children_views.remove();
        },
    });


    var FlexBoxView = BoxView.extend({
        render: function(){
            FlexBoxView.__super__.render.apply(this);
            this.listenTo(this.model, 'change:orientation', this.update_orientation, this);
            this.listenTo(this.model, 'change:flex', this._flex_changed, this);
            this.listenTo(this.model, 'change:pack', this._pack_changed, this);
            this.listenTo(this.model, 'change:align', this._align_changed, this);
            this._flex_changed();
            this._pack_changed();
            this._align_changed();
            this.update_orientation();
        },

        update_orientation: function(){
            var orientation = this.model.get("orientation");
            if (orientation == "vertical") {
                this.$box.removeClass("hbox").addClass("vbox");
            } else {
                this.$box.removeClass("vbox").addClass("hbox");
            }
        },

        _flex_changed: function(){
            if (this.model.previous('flex')) {
                this.$box.removeClass('box-flex' + this.model.previous('flex'));
            }
            this.$box.addClass('box-flex' + this.model.get('flex'));
        },

        _pack_changed: function(){
            if (this.model.previous('pack')) {
                this.$box.removeClass(this.model.previous('pack'));
            }
            this.$box.addClass(this.model.get('pack'));
        },

        _align_changed: function(){
            if (this.model.previous('align')) {
                this.$box.removeClass('align-' + this.model.previous('align'));
            }
            this.$box.addClass('align-' + this.model.get('align'));
        },
    });

    return {
        'unpack_models': unpack_models,
        'BoxModel': BoxModel,
        'BoxView': BoxView,
        'FlexBoxView': FlexBoxView,
    };
});
