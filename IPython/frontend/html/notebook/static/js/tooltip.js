//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Tooltip
//============================================================================

// Todo : 
// use codemirror highlight example to 
// highlight the introspection request and introspect on mouse hove ...
//
//
var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Tooltip = function (notebook) {
        this.tooltip = $('#tooltip');
        var that = this;
        this._hidden = true;

        // variable for consecutive call
        this._old_cell = null ;
        this._old_request = null ;
        this._consecutive_conter = 0;

        // 'sticky ?'
        this._sticky = false;

        // contain the button in the upper right corner
        this.buttons = $('<div/>')
              .addClass('tooltipbuttons');

        // will contain the docstring 
        this.text    = $('<div/>')
          .addClass('tooltiptext')
          .addClass('smalltooltip');
        
        var tooltip = this.tooltip;

	// build the buttons menu on the upper right
        
	// expand the tooltip to see more
        var expandlink=$('<a/>').attr('href',"#")
              .addClass("ui-corner-all") //rounded corner
              .attr('role',"button")
              .attr('id','expanbutton')
              .click(function(){that.expand()})
            .append(
        $('<span/>').text('Expand')
            .addClass('ui-icon')
            .addClass('ui-icon-plus')
        );

        // open in pager
        var morelink=$('<a/>').attr('href',"#")
            .attr('role',"button")
            .addClass('ui-button');
        var morespan=$('<span/>').text('Open in Pager')
            .addClass('ui-icon')
            .addClass('ui-icon-arrowstop-l-n');
        morelink.append(morespan);
        morelink.click(function(){
            that.showInPager();
        });

        // close the tooltip
        var closelink=$('<a/>').attr('href',"#");
            closelink.attr('role',"button");
            closelink.addClass('ui-button');
        var closespan=$('<span/>').text('Close');
            closespan.addClass('ui-icon');
            closespan.addClass('ui-icon-close');
        closelink.append(closespan);
        closelink.click(function(){
        that.hide();
            });
        
        //construct the tooltip
        // add in the reverse order you want them to appear
        this.buttons.append(closelink);
        this.buttons.append(expandlink);
        this.buttons.append(morelink);

        // we need a phony element to make the small arrow
        // of the tooltip in css
        // we could try to move the arrow later
        this.arrow = $('<div/>').addClass('pretooltiparrow');
        this.tooltip.append(this.buttons);
        this.tooltip.append(this.arrow);
        this.tooltip.append(this.text);
    };

    Tooltip.prototype.showInPager = function()
    {
            var msg_id = IPython.notebook.kernel.execute(that.name+"?");
            IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
            this.remove_and_cancel_tooltip();
            this._cmfocus();
    }


    Tooltip.prototype.expand = function(){
        this.text.removeClass('smalltooltip');
        this.text.addClass('bigtooltip');
        $('#expanbutton').addClass('hidden');
        this._cmfocus();
    }

    // deal with all the logic of hiding the tooltip
    // and reset it's status
    Tooltip.prototype.hide = function()
    {
         this.tooltip.addClass('hide');
         $('#expanbutton').removeClass('hidden');
         this.text.removeClass('bigtooltip');
         this.text.addClass('smalltooltip');
         // keep scroll top to be sure to always see the first line
         this.text.scrollTop(0);
         this._hidden = true;
    }

    //TODO, try to diminish the number of parameters.
    Tooltip.prototype.request_tooltip_after_time = function (pre_cursor,time){
    };


    Tooltip.prototype.remove_and_cancel_tooltip = function(force) {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        if(this._sticky == false || force == true)
        {
            this.hide();
        }
        this.cancel_pending();
        this._old_cell = null ;
        this._old_request = null ;
        this._consecutive_conter = 0;
    }

    Tooltip.prototype.cancel_pending = function(){
        if (this.tooltip_timeout != null){
            clearTimeout(this.tooltip_timeout);
            this.tooltip_timeout = null;
        }
    }
    
    Tooltip.prototype.pending = function(cell,text)
    {
        var that = this;
        this.tooltip_timeout = setTimeout(function(){that.request(cell)} , IPython.notebook.time_before_tooltip);
    }
    Tooltip.prototype.request = function(cell)
    {
        this.cancel_pending();
        var editor = cell.code_mirror;
        this.code_mirror = editor;
        var cursor = editor.getCursor();
        var text = editor.getRange({line:cursor.line,ch:0},cursor).trim();

        if( this._old_cell == cell && this._old_request == text && this._hidden == false)
        {
            this._consecutive_conter = this._consecutive_conter +1;
        } else {
            this._old_cell = cell ;
            this._old_request = text ;
            this._consecutive_conter =0;
            this.cancel_stick();
        }

        if( this._consecutive_conter == 1 )
        {
            this.expand()
            return;
        }
        else if( this._consecutive_conter ==  2)
        {
            this.stick();
            return;
        }
        else if( this._consecutive_conter ==  3)
        {
            console.log('should open in pager');
            this._old_cell = null ;
            this._cancel_stick 
            this._old_request = null ;
            this._consecutive_conter = 0;
            this.showInPager();
            this._cmfocus();
            return;
        }
        else if( this._consecutive_conter ==  4)
        {

        }

        if (text === "" || text === "(" ) {
            return;
            // don't do anything if line beggin with '(' or is empty
        }
        IPython.notebook.request_tool_tip(cell, text);
    }
    Tooltip.prototype.cancel_stick = function()
    {
            clearTimeout(this._stick_timeout);
            this._sticky = false;
    }

    Tooltip.prototype.stick = function() 
    {
        console.log('tooltip will stick for at least 10 sec');
        var that = this; 
        this._sticky = true;
        this._stick_timeout = setTimeout( function(){
            that._sticky = false;
            console.log('tooltip will not stick anymore');
            }, 10*1000
        );


    }

    Tooltip.prototype.show = function(reply, codecell)
    {
        // move the bubble if it is not hidden
        // otherwise fade it
        var editor = codecell.code_mirror;
        this.name = reply.name;
        this.code_mirror = editor;

        // do some math to have the tooltip arrow on more or less on left or right
        // width of the editor
        var w= $(this.code_mirror.getScrollerElement()).width();
        // ofset of the editor
        var o= $(this.code_mirror.getScrollerElement()).offset();
        var pos = editor.cursorCoords();
        var xinit = pos.x;
        var xinter = o.left + (xinit-o.left)/w*(w-450);
        var posarrowleft = xinit - xinter;
        

        if( this._hidden == false)
        {
            this.tooltip.animate({'left' : xinter-30+'px','top' :(pos.yBot+10)+'px'});
        } else 
        {
            this.tooltip.css({'left' : xinter-30+'px'});
            this.tooltip.css({'top' :(pos.yBot+10)+'px'});
        }
        this.arrow.animate({'left' : posarrowleft+'px'});
        this.tooltip.removeClass('hidden')
        this.tooltip.removeClass('hide');
        this._hidden = false;

        // build docstring
        defstring = reply.call_def;
        if (defstring == null) { defstring = reply.init_definition; }
        if (defstring == null) { defstring = reply.definition; }

        docstring = reply.call_docstring;
        if (docstring == null) { docstring = reply.init_docstring; }
        if (docstring == null) { docstring = reply.docstring; }
        if (docstring == null) { docstring = "<empty docstring>"; }

        this.text.children().remove();

        var pre=$('<pre/>').html(utils.fixConsole(docstring));
        if(defstring){
            var defstring_html = $('<pre/>').html(utils.fixConsole(defstring));
            this.text.append(defstring_html);
        }
        this.text.append(pre);
        // keep scroll top to be sure to always see the first line
        this.text.scrollTop(0);


    }

    Tooltip.prototype.showInPager = function(text){
        var msg_id = IPython.notebook.kernel.execute(this.name+"?");
        IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
        this.remove_and_cancel_tooltip(true);
        this._cmfocus();
    }

    Tooltip.prototype._cmfocus = function()
    {
        var cm = this.code_mirror;
        setTimeout(function(){cm.focus();}, 50);
    }


    IPython.Tooltip = Tooltip;

    return IPython;
}(IPython));
