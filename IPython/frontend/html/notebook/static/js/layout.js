//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Layout
//============================================================================

var IPython = (function (IPython) {

    var LayoutManager = function () {
        this.bind_events();
    };


    LayoutManager.prototype.bind_events = function () {
        $(window).resize($.proxy(this.do_resize,this));
    };


    LayoutManager.prototype.do_resize = function () {
        var win = $(window);
        var w = win.width();
        var h = win.height();
        var header_height = $('div#header').outerHeight(true);
        var app_height = h - header_height - 2;  // content height

        $('div#main_app').height(app_height + 2);  // content+padding+border height

        $('div#left_panel').height(app_height);

        $('div#left_panel_splitter').height(app_height);

        $('div#notebook_panel').height(app_height);
        var left_panel_width = $('div#left_panel').outerWidth();
        var left_panel_splitter_width = $('div#left_panel_splitter').outerWidth();
        if (IPython.left_panel.expanded) {
            $('div#notebook_panel').css({marginLeft : left_panel_width+left_panel_splitter_width});
        } else {
        $('div#notebook_panel').css({marginLeft : left_panel_splitter_width});
        }


        var pager_height = IPython.pager.percentage_height*app_height;
        var pager_splitter_height = $('div#pager_splitter').outerHeight(true);
        $('div#pager').height(pager_height);
        if (IPython.pager.expanded) {
            $('div#notebook').height(app_height-pager_height-pager_splitter_height);
        } else {
            $('div#notebook').height(app_height-pager_splitter_height);
        }
    };

    IPython.LayoutManager = LayoutManager;

    return IPython;

}(IPython));
