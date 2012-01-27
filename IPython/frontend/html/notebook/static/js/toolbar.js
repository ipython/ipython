//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
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
            this.bind_events();
        }
    };


    ToolBar.prototype.style = function () {
        this.element.addClass('border-box-sizing');
        this.element.find('#save_b').button({
            icons : {primary: 'ui-icon-disk'},
            text : false
        });
        this.element.find('#cut_b').button({
            icons: {primary: 'ui-icon-scissors'},
            text : false
        });
        this.element.find('#copy_b').button({
            icons: {primary: 'ui-icon-copy'},
            text : false
        });
        this.element.find('#paste_b').button({
            icons: {primary: 'ui-icon-clipboard'},
            text : false
        });
        this.element.find('#cut_copy_paste').buttonset();
        this.element.find('#move_up_b').button({
            icons: {primary: 'ui-icon-arrowthick-1-n'},
            text : false
        });
        this.element.find('#move_down_b').button({
            icons: {primary: 'ui-icon-arrowthick-1-s'},
            text : false
        });
        this.element.find('#move_up_down').buttonset();
        this.element.find('#insert_above_b').button({
            icons: {primary: 'ui-icon-arrowthickstop-1-n'},
            text : false
        });
        this.element.find('#insert_below_b').button({
            icons: {primary: 'ui-icon-arrowthickstop-1-s'},
            text : false
        });
        this.element.find('#insert_above_below').buttonset();
        this.element.find('#run_b').button({
            icons: {primary: 'ui-icon-play'},
            text : false
        });
        this.element.find('#interrupt_b').button({
            icons: {primary: 'ui-icon-stop'},
            text : false
        });
        this.element.find('#run_int').buttonset();
    };


    ToolBar.prototype.bind_events = function () {

    };


    IPython.ToolBar = ToolBar;

    return IPython;

}(IPython));
