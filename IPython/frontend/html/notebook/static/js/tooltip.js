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
var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Tooltip = function (notebook) {
        this.tooltip = $('#tooltip');
	
	// contain the button in the upper right corner
        this.buttons = $('<div/>')
              .addClass('tooltipbuttons');
	
	// will contain the docstring 
        this.text    = $('<div/>')
          .addClass('tooltiptext')
          .addClass('smalltooltip');
        
        var tooltip = this.tooltip;
        var text = this.text;

	// build the buttons menu on the upper right
        
	// expand the tooltip to see more
	var expandspan=$('<span/>').text('Expand')
            .addClass('ui-icon')
            .addClass('ui-icon-plus');
        var expandlink=$('<a/>').attr('href',"#")
              .addClass("ui-corner-all") //rounded corner
              .attr('role',"button")
              .attr('id','expanbutton')
              .append(expandspan)
              .click(function(){
                  text.removeClass('smalltooltip');
                  text.addClass('bigtooltip');
                  $('#expanbutton').remove();
                  //setTimeout(function(){that.code_mirror.focus();}, 50);
              });

	// open in pager
        var morelink=$('<a/>').attr('href',"#");
            morelink.attr('role',"button");
            morelink.addClass('ui-button');
        var morespan=$('<span/>').text('Open in Pager');
            morespan.addClass('ui-icon');
            morespan.addClass('ui-icon-arrowstop-l-n');
        morelink.append(morespan);
        morelink.click(function(){
            var msg_id = IPython.notebook.kernel.execute(name+"?");
            IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
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
            tooltip.addClass('hide');
            });
        
	//construct the tooltip
	// add in the reverse order you want them to appear
        this.buttons.append(closelink);
        this.buttons.append(expandlink);
        this.buttons.append(morelink);
	
	// we need a phony element to make the small arrow
	// of the tooltip in css
	// we could try to move the arrow later
        arrow = $('<div/>').addClass('pretooltiparrow');
        this.tooltip.append(arrow);
        this.tooltip.append(this.buttons);
        this.tooltip.append(this.text);
    };



    //TODO, try to diminish the number of parameters.
    Tooltip.prototype.request_tooltip_after_time = function (pre_cursor,time){
    };


    Tooltip.prototype.remove_and_cancel_tooltip = function() {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        if (this.tooltip_timeout != null){
            clearTimeout(this.tooltip_timeout);
            $('#tooltip').remove();
            this.tooltip_timeout = null;
        }
    }
    Tooltip.prototype.show = function(reply,pos)
    {
        this.tooltip.css('left',pos.x-30+'px');
        this.tooltip.css('top',(pos.yBot+10)+'px');
    	this.tooltip.removeClass('hidden')
    	this.tooltip.removeClass('hide');

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
        this.text.append(pre)


    }	

    Tooltip.prototype.showInPager = function(){
        var msg_id = IPython.notebook.kernel.execute(name+"?");
        IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
        that.remove_and_cancel_tooltip();
        setTimeout(function(){that.code_mirror.focus();}, 50);
    }

    Tooltip.prototype.finish_tooltip = function (reply) {

        var expandlink=$('<a/>').attr('href',"#");
            expandlink.addClass("ui-corner-all"); //rounded corner
            expandlink.attr('role',"button");

        var expandspan=$('<span/>').text('Expand');
            expandspan.addClass('ui-icon');
            expandspan.addClass('ui-icon-plus');

        expandlink.append(expandspan);
        expandlink.attr('id','expanbutton');
        expandlink.click(function(){
            tooltip.removeClass('smalltooltip');
            tooltip.addClass('bigtooltip');
            $('#expanbutton').remove();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        });

        var morelink=$('<a/>').attr('href',"#");
            morelink.attr('role',"button");
            morelink.addClass('ui-button');
        var morespan=$('<span/>').text('Open in Pager');
            morespan.addClass('ui-icon');
            morespan.addClass('ui-icon-arrowstop-l-n');
        morelink.append(morespan);
        morelink.click(function(){
            this.showInPager();
        });


        var closelink=$('<a/>').attr('href',"#");
            closelink.attr('role',"button");
            closelink.addClass('ui-button');

        var closespan=$('<span/>').text('Close');
            closespan.addClass('ui-icon');
            closespan.addClass('ui-icon-close');
        closelink.append(closespan);
        closelink.click(function(){
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
            });
        //construct the tooltip
        tooltip.append(closelink);
        tooltip.append(expandlink);
        tooltip.append(morelink);
        
        var pos = this.code_mirror.cursorCoords();
        tooltip.css('left',pos.x+'px');
        tooltip.css('top',pos.yBot+'px');

    };


    IPython.Tooltip = Tooltip;

    return IPython;
}(IPython));
