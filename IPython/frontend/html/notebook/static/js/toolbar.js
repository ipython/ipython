//----------------------------------------------------------------------------
//  Copyright (C) 2008 The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// ToolBar
//============================================================================

var IPython = (function (IPython) {

    var ToolBar = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.style();
        }
    };

    // add a group of button into the current toolbar.
    //
    // First argument : Mandatory
    //      list of dict as argument, each dict should contain
    //      3 mandatory keys and values :
    //      label : string -- the text to show on hover
    //      icon  : string -- the jQuery-ui icon to add on this button
    //      callback : function -- the callback to execute on a click
    //
    //      and optionally an 'id' key that is assigned to the button element
    //
    // Second Argument, optional,
    //      string reprensenting the id to give to the button group.
    //
    // Example
    //
    // IPython.toolbar.add_button_group([
    //  {label:'my button',
    //   icon:'ui-icon-disk',
    //   callback:function(){alert('hoho'),
    //   id : 'my_button_id',                 // this is optional
    //   }
    //  },
    //  {label:'my second button',
    //   icon:'ui-icon-scissors',
    //   callback:function(){alert('be carefull I cut')}
    //  }
    //  ],
    //  "my_button_group_id"
    //  )
    //
    ToolBar.prototype.add_button_group = function(list, group_id){
        var span_group = $('<span/>');
        if( group_id != undefined )
            span_group.attr('id',group_id)
        for(var el in list)
        {
            var button  = $('<button/>').button({
                icons : {primary: list[el].icon},
                text : false,
                label: list[el].label,
                });
            var id = list[el].id;
            if( id != undefined )
                button.attr('id',id);
            var fun = list[el].callback;
            button.click(fun);
            span_group.append(button);
        }
        span_group.buttonset();
        $(this.selector).append(span_group)
    }

    ToolBar.prototype.style = function () {
        this.element.addClass('border-box-sizing').
            addClass('ui-widget ui-widget-content toolbar').
            css('border-top-style','none').
            css('border-left-style','none').
            css('border-right-style','none');
    };


    ToolBar.prototype.toggle = function () {
        this.element.toggle();
        IPython.layout_manager.do_resize();
    };


    IPython.ToolBar = ToolBar;

    return IPython;

}(IPython));
