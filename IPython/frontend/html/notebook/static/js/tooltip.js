//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------
//============================================================================
// Tooltip
//============================================================================
//
// you can set the autocall time by setting `IPython.tooltip.time_before_tooltip` in ms
//
// you can configure the differents action of pressing tab several times in a row by
// setting/appending different fonction in the array
// IPython.tooltip.tabs_functions
//
// eg :
// IPython.tooltip.tabs_functions[4] = function (){console.log('this is the action of the 4th tab pressing')}
//
var IPython = (function (IPython) {
    "use strict";

    var utils = IPython.utils;

    // tooltip constructor
    var Tooltip = function () {
            var that = this;
            this.time_before_tooltip = 1200;

            // handle to html
            this.tooltip = $('#tooltip');
            this._hidden = true;

            // variable for consecutive call
            this._old_cell = null;
            this._old_request = null;
            this._consecutive_counter = 0;

            // 'sticky ?'
            this._sticky = false;

            // contain the button in the upper right corner
            this.buttons = $('<div/>').addClass('tooltipbuttons');

            // will contain the docstring
            this.text = $('<div/>').addClass('tooltiptext').addClass('smalltooltip');

            // build the buttons menu on the upper right
            // expand the tooltip to see more
            var expandlink = $('<a/>').attr('href', "#").addClass("ui-corner-all") //rounded corner
            .attr('role', "button").attr('id', 'expanbutton').attr('title', 'Grow the tooltip vertically (press tab 2 times)').click(function () {
                that.expand()
            }).append(
            $('<span/>').text('Expand').addClass('ui-icon').addClass('ui-icon-plus'));

            // open in pager
            var morelink = $('<a/>').attr('href', "#").attr('role', "button").addClass('ui-button').attr('title', 'show the current docstring in pager (press tab 4 times)');
            var morespan = $('<span/>').text('Open in Pager').addClass('ui-icon').addClass('ui-icon-arrowstop-l-n');
            morelink.append(morespan);
            morelink.click(function () {
                that.showInPager();
            });

            // close the tooltip
            var closelink = $('<a/>').attr('href', "#").attr('role', "button").addClass('ui-button');
            var closespan = $('<span/>').text('Close').addClass('ui-icon').addClass('ui-icon-close');
            closelink.append(closespan);
            closelink.click(function () {
                that.remove_and_cancel_tooltip(true);
            });

            this._clocklink = $('<a/>').attr('href', "#");
            this._clocklink.attr('role', "button");
            this._clocklink.addClass('ui-button');
            this._clocklink.attr('title', 'Tootip is not dismissed while typing for 10 seconds');
            var clockspan = $('<span/>').text('Close');
            clockspan.addClass('ui-icon');
            clockspan.addClass('ui-icon-clock');
            this._clocklink.append(clockspan);
            this._clocklink.click(function () {
                that.cancel_stick();
            });




            //construct the tooltip
            // add in the reverse order you want them to appear
            this.buttons.append(closelink);
            this.buttons.append(expandlink);
            this.buttons.append(morelink);
            this.buttons.append(this._clocklink);
            this._clocklink.hide();


            // we need a phony element to make the small arrow
            // of the tooltip in css
            // we will move the arrow later
            this.arrow = $('<div/>').addClass('pretooltiparrow');
            this.tooltip.append(this.buttons);
            this.tooltip.append(this.arrow);
            this.tooltip.append(this.text);

            // function that will be called if you press tab 1, 2, 3... times in a row
            this.tabs_functions = [function (cell, text) {
                that._request_tooltip(cell, text);
            }, function () {
                that.expand();
            }, function () {
                that.stick();
            }, function (cell) {
                that.cancel_stick();
                that.showInPager(cell);
            }];
            // call after all the tabs function above have bee call to clean their effects
            // if necessary
            this.reset_tabs_function = function (cell, text) {
                this._old_cell = (cell) ? cell : null;
                this._old_request = (text) ? text : null;
                this._consecutive_counter = 0;
            }
        };

    Tooltip.prototype.showInPager = function (cell) {
        // reexecute last call in pager by appending ? to show back in pager
        var that = this;
        var empty = function () {};
        cell.kernel.execute(
        that.name + '?', {
            'execute_reply': empty,
            'output': empty,
            'clear_output': empty,
            'cell': cell
        }, {
            'silent': false
        });
        this.remove_and_cancel_tooltip();
    }

    // grow the tooltip verticaly
    Tooltip.prototype.expand = function () {
        this.text.removeClass('smalltooltip');
        this.text.addClass('bigtooltip');
        $('#expanbutton').hide('slow');
    }

    // deal with all the logic of hiding the tooltip
    // and reset it's status
    Tooltip.prototype._hide = function () {
        this.tooltip.fadeOut('fast');
        $('#expanbutton').show('slow');
        this.text.removeClass('bigtooltip');
        this.text.addClass('smalltooltip');
        // keep scroll top to be sure to always see the first line
        this.text.scrollTop(0);
        this._hidden = true;
        this.code_mirror = null;
    }

    Tooltip.prototype.remove_and_cancel_tooltip = function (force) {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        if (this._sticky == false || force == true) {
            this.cancel_stick();
            this._hide();
        }
        this.cancel_pending();
        this.reset_tabs_function();
    }

    // cancel autocall done after '(' for example.
    Tooltip.prototype.cancel_pending = function () {
        if (this._tooltip_timeout != null) {
            clearTimeout(this._tooltip_timeout);
            this._tooltip_timeout = null;
        }
    }

    // will trigger tooltip after timeout
    Tooltip.prototype.pending = function (cell) {
        var that = this;
        this._tooltip_timeout = setTimeout(function () {
            that.request(cell)
        }, that.time_before_tooltip);
    }

    Tooltip.prototype._request_tooltip = function (cell, func) {
        // use internally just to make the request to the kernel
        // Feel free to shorten this logic if you are better
        // than me in regEx
        // basicaly you shoul be able to get xxx.xxx.xxx from
        // something(range(10), kwarg=smth) ; xxx.xxx.xxx( firstarg, rand(234,23), kwarg1=2,
        // remove everything between matchin bracket (need to iterate)
        var matchBracket = /\([^\(\)]+\)/g;
        var endBracket = /\([^\(]*$/g;
        var oldfunc = func;

        func = func.replace(matchBracket, "");
        while (oldfunc != func) {
            oldfunc = func;
            func = func.replace(matchBracket, "");
        }
        // remove everything after last open bracket
        func = func.replace(endBracket, "");

        var re = /[a-z_][0-9a-z._]+$/gi; // casse insensitive
        var callbacks = {
            'object_info_reply': $.proxy(this._show, this)
        }
        var msg_id = cell.kernel.object_info_request(re.exec(func), callbacks);
    }

    // make an imediate completion request
    Tooltip.prototype.request = function (cell) {
        // request(codecell)
        // Deal with extracting the text from the cell and counting
        // call in a row
        this.cancel_pending();
        var editor = cell.code_mirror;
        var cursor = editor.getCursor();
        var text = editor.getRange({
            line: cursor.line,
            ch: 0
        }, cursor).trim();

        if(editor.somethingSelected()){
            text = editor.getSelection();
        }

        // need a permanent handel to code_mirror for future auto recall
        this.code_mirror = editor;

        // now we treat the different number of keypress
        // first if same cell, same text, increment counter by 1
        if (this._old_cell == cell && this._old_request == text && this._hidden == false) {
            this._consecutive_counter++;
        } else {
            // else reset
            this.cancel_stick();
            this.reset_tabs_function (cell, text);
        }

        // don't do anything if line beggin with '(' or is empty
        if (text === "" || text === "(") {
            return;
        }

        this.tabs_functions[this._consecutive_counter](cell, text);

        // then if we are at the end of list function, reset
        if (this._consecutive_counter == this.tabs_functions.length) this.reset_tabs_function (cell, text);

        return;
    }

    // cancel the option of having the tooltip to stick
    Tooltip.prototype.cancel_stick = function () {
        clearTimeout(this._stick_timeout);
        this._stick_timeout = null;
        this._clocklink.hide('slow');
        this._sticky = false;
    }

    // put the tooltip in a sicky state for 10 seconds
    // it won't be removed by remove_and_cancell() unless you called with
    // the first parameter set to true.
    // remove_and_cancell_tooltip(true)
    Tooltip.prototype.stick = function (time) {
        time = (time != undefined) ? time : 10;
        var that = this;
        this._sticky = true;
        this._clocklink.show('slow');
        this._stick_timeout = setTimeout(function () {
            that._sticky = false;
            that._clocklink.hide('slow');
        }, time * 1000);
    }

    // should be called with the kernel reply to actually show the tooltip
    Tooltip.prototype._show = function (reply) {
        // move the bubble if it is not hidden
        // otherwise fade it
        this.name = reply.name;

        // do some math to have the tooltip arrow on more or less on left or right
        // width of the editor
        var w = $(this.code_mirror.getScrollerElement()).width();
        // ofset of the editor
        var o = $(this.code_mirror.getScrollerElement()).offset();

        // whatever anchor/head order but arrow at mid x selection
        var anchor = this.code_mirror.cursorCoords(false);
        var head  = this.code_mirror.cursorCoords(true);
        var pos = {};
        pos.y = head.top
        pos.yBot = head.bottom
        pos.x = (head.left+anchor.left)/2;

        var xinit = pos.x;
        var xinter = o.left + (xinit - o.left) / w * (w - 450);
        var posarrowleft = xinit - xinter;


        if (this._hidden == false) {
            this.tooltip.animate({
                'left': xinter - 30 + 'px',
                'top': (pos.yBot + 10) + 'px'
            });
        } else {
            this.tooltip.css({
                'left': xinter - 30 + 'px'
            });
            this.tooltip.css({
                'top': (pos.yBot + 10) + 'px'
            });
        }
        this.arrow.animate({
            'left': posarrowleft + 'px'
        });
        this.tooltip.fadeIn('fast');
        this._hidden = false;

        // build docstring
        var defstring = reply.call_def;
        if (defstring == null) {
            defstring = reply.init_definition;
        }
        if (defstring == null) {
            defstring = reply.definition;
        }

        var docstring = reply.call_docstring;
        if (docstring == null) {
            docstring = reply.init_docstring;
        }
        if (docstring == null) {
            docstring = reply.docstring;
        }
        if (docstring == null) {
            docstring = "<empty docstring>";
        }

        this.text.children().remove();

        var pre = $('<pre/>').html(utils.fixConsole(docstring));
        if (defstring) {
            var defstring_html = $('<pre/>').html(utils.fixConsole(defstring));
            this.text.append(defstring_html);
        }
        this.text.append(pre);
        // keep scroll top to be sure to always see the first line
        this.text.scrollTop(0);
    }


    IPython.Tooltip = Tooltip;

    return IPython;

}(IPython));
