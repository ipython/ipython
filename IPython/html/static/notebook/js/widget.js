//----------------------------------------------------------------------------
//  Copyright (C) 2013  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Cell
//============================================================================
/**
 * An extendable module that provide base functionnality to create cell for notebook.
 * @module IPython
 * @namespace IPython
 * @submodule widget
 */

var IPython = (function (IPython) {
    "use strict";

    //-----------------------------------------------------------------------
    // WidgetManager class
    //-----------------------------------------------------------------------
    
    var WidgetManager = function (kernel) {
        this.widgets = {};
        this.widget_types = {widget : Widget};
        if (kernel !== undefined) {
            this.init_kernel(kernel);
        }
    };
    
    WidgetManager.prototype.init_kernel = function (kernel) {
        this.kernel = kernel;
        var msg_types = ['widget_create', 'widget_destroy', 'widget_update'];
        for (var i = 0; i < msg_types.length; i++) {
            var msg_type = msg_types[i];
            kernel.register_iopub_handler(msg_type, $.proxy(this['handle_' + msg_type], this));
        }
    };
    
    WidgetManager.prototype.register_widget_type = function (widget_type, constructor) {
        // Register a constructor for a given widget type name
        this.widget_types[widget_type] = constructor;
    };
    
    WidgetManager.prototype.handle_widget_create = function (msg) {
        var content = msg.content;
        console.log("handle create", content);
        console.log(this.widget_types);
        var constructor = this.widget_types[content.widget_type];
        if (constructor === undefined) {
            console.log("No such widget type registered: ", content.widget_type);
            console.log("Available widget types are: ", this.widget_types);
            return;
        }
        var widget = new constructor(this.kernel, content);
        this.widgets[content.widget_id] = widget;
    };
    
    WidgetManager.prototype.handle_widget_destroy = function (msg) {
        var content = msg.content;
        console.log("handle destroy", content);
        var widget = this.widgets[content.widget_id];
        if (widget === undefined) {
            return;
        }
        delete this.widgets[content.widget_id];
        widget.handle_destroy(content.data);
    };
    
    WidgetManager.prototype.handle_widget_update = function (msg) {
        var content = msg.content;
        console.log("handle update", content);
        var widget = this.widgets[content.widget_id];
        if (widget === undefined) {
            return;
        }
        widget.handle_update(content.data);
    };
    
    //-----------------------------------------------------------------------
    // Widget base class
    //-----------------------------------------------------------------------
    
    var Widget = function (kernel, content) {
        console.log('widget!', this, kernel, content);
        this.kernel = kernel;
        this.widget_id = content.widget_id;
        this.handle_create(content.data);
    };
    
    Widget.prototype.handle_create = function (data) {
        // base class init does nothing
        console.log("handle_create", this, data);
    };
    
    Widget.prototype.handle_update = function (data) {
        console.log("handle_update", this, data);
    };
    
    Widget.prototype.handle_destroy = function (data) {
        console.log("handle_destroy", this, data);
    };
    
    Widget.prototype.update = function (data) {
        console.log("update", this, data);
        var content = {
            widget_id : this.widget_id,
            data : data,
        };
        this.kernel.send_shell_message("widget_update", content);
    };
    
    
    Widget.prototype.destroy = function (data) {
        console.log("destroy", this, data);
        var content = {
            widget_id : this.widget_id,
            data : data,
        };
        this.kernel.send_shell_message("widget_destroy", content);
    };
    
    IPython.WidgetManager = WidgetManager;
    IPython.Widget = Widget;

    return IPython;

}(IPython));

