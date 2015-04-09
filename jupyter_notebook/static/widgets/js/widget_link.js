// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "widgets/js/widget",
    "jquery",
], function(widget, $){
    var LinkModel = widget.WidgetModel.extend({
        initialize: function() {
            this.on("change:widgets", function(model, value, options) {
                this.update_bindings(model.previous("widgets") || [], value);
                this.update_value(this.get("widgets")[0]);
            }, this);
            this.once("destroy", function(model, collection, options) {
                this.update_bindings(this.get("widgets"), []);
            }, this);
        },
        update_bindings: function(oldlist, newlist) {
            var that = this;
            _.each(oldlist, function(elt) {elt[0].off("change:" + elt[1], null, that);});
            _.each(newlist, function(elt) {elt[0].on("change:" + elt[1],
                                                     function(model, value, options) {
                                                         that.update_value(elt);
                                                     }, that);
                                           // TODO: register for any destruction handlers
                                           // to take an item out of the list
                                          });
        },
        update_value: function(elt) {
            if (this.updating) {return;}
            var model = elt[0];
            var attr = elt[1];
            var new_value = model.get(attr);
            this.updating = true;
            _.each(_.without(this.get("widgets"), elt),
                   function(element, index, list) {
                       if (element[0]) {
                           element[0].set(element[1], new_value);
                           element[0].save_changes();
                       }
                   }, this);
            this.updating = false;
        },
    });

    var DirectionalLinkModel = widget.WidgetModel.extend({
        initialize: function() {
            this.on("change", this.update_bindings, this);
            this.once("destroy", function() {
                if (this.source) {
                    this.source[0].off("change:" + this.source[1], null, this);
                }
            }, this);
        },
        update_bindings: function() {
            if (this.source) {
                this.source[0].off("change:" + this.source[1], null, this);
            }
            this.source = this.get("source");
            if (this.source) {
                this.source[0].on("change:" + this.source[1], function() { this.update_value(this.source); }, this);
                this.update_value(this.source);
            }
        },
        update_value: function(elt) {
            if (this.updating) {return;}
            var model = elt[0];
            var attr = elt[1];
            var new_value = model.get(attr);
            this.updating = true;
            _.each(this.get("targets"),
                   function(element, index, list) {
                       if (element[0]) {
                           element[0].set(element[1], new_value);
                           element[0].save_changes();
                       }
                   }, this);
            this.updating = false;
        },
    });

    return {
        "LinkModel": LinkModel,
        "DirectionalLinkModel": DirectionalLinkModel,
    }
});
