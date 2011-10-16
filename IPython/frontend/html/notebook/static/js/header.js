//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// HeaderSection
//============================================================================

var IPython = (function (IPython) {

    var HeaderSection = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.content = this.element.find('div.header');
	    this.style();
            this.bind_events();
        }
    };

    HeaderSection.prototype.style = function () {
	this.content.addClass('ui-helper-clearfix');
	this.content.find('#quick_help').button();
    };

    HeaderSection.prototype.bind_events = function () {
        var that = this;
        this.content.find('#quick_help').click(function () {
            IPython.notebook.show_keyboard_shortcuts();
        });
    };

    // Set module variables
    IPython.HeaderSection = HeaderSection;

    return IPython;

}(IPython));
