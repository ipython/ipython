//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Pager
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var Pager = function (pager_selector, pager_splitter_selector) {
        this.pager_element = $(pager_selector);
        this.pager_button_area = $('#pager_button_area');
        var that = this;
        this.percentage_height = 0.40;
        this.pager_splitter_element = $(pager_splitter_selector)
            .draggable({
                        containment: 'window',
                        axis:'y',
                        helper: null ,
                        drag: function(event, ui) {
                            // recalculate the amount of space the pager should take
                            var pheight = ($(document.body).height()-event.clientY-4);
                            var downprct = pheight/IPython.layout_manager.app_height();
                                downprct = Math.min(0.9, downprct);
                            if (downprct < 0.1) {
                                that.percentage_height = 0.1;
                                that.collapse({'duration':0});
                            } else if (downprct > 0.2) {
                                that.percentage_height = downprct;
                                that.expand({'duration':0});
                            }
                            IPython.layout_manager.do_resize();
                       }
            });
        this.expanded = false;
        this.style();
        this.create_button_area();
        this.bind_events();
    };

    Pager.prototype.create_button_area = function(){
        var that = this;
        this.pager_button_area.append(
            $('<a>').attr('role', "button")
                    .attr('title',"Open the pager in an external window")
                    .addClass('ui-button')
                    .click(function(){that.detach()})
                    .attr('style','position: absolute; right: 20px;')
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-extlink")
                    )
        )
        this.pager_button_area.append(
            $('<a>').attr('role', "button")
                    .attr('title',"Close the pager")
                    .addClass('ui-button')
                    .click(function(){that.collapse()})
                    .attr('style','position: absolute; right: 5px;')
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-close")
                    )
        )
    };

    Pager.prototype.style = function () {
        this.pager_splitter_element.addClass('border-box-sizing ui-widget ui-state-default');
        this.pager_element.addClass('border-box-sizing');
        this.pager_element.find(".container").addClass('border-box-sizing');
        this.pager_splitter_element.attr('title', 'Click to Show/Hide pager area, drag to Resize');
    };


    Pager.prototype.bind_events = function () {
        var that = this;

        this.pager_element.bind('collapse_pager', function (event, extrap) {
            var time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            that.pager_element.hide(time);
        });

        this.pager_element.bind('expand_pager', function (event, extrap) {
            var time = (extrap != undefined) ? ((extrap.duration != undefined ) ? extrap.duration : 'fast') : 'fast';
            that.pager_element.show(time);
        });

        this.pager_splitter_element.hover(
            function () {
                that.pager_splitter_element.addClass('ui-state-hover');
            },
            function () {
                that.pager_splitter_element.removeClass('ui-state-hover');
            }
        );

        this.pager_splitter_element.click(function () {
            that.toggle();
        });

        $([IPython.events]).on('open_with_text.Pager', function (event, data) {
            if (data.text.trim() !== '') {
                that.clear();
                that.expand();
                that.append_text(data.text);
            };
        });
    };


    Pager.prototype.collapse = function (extrap) {
        if (this.expanded === true) {
            this.expanded = false;
            this.pager_element.add($('div#notebook')).trigger('collapse_pager', extrap);
        };
    };


    Pager.prototype.expand = function (extrap) {
        if (this.expanded !== true) {
            this.expanded = true;
            this.pager_element.add($('div#notebook')).trigger('expand_pager', extrap);
        };
    };


    Pager.prototype.toggle = function () {
        if (this.expanded === true) {
            this.collapse();
        } else {
            this.expand();
        };
    };


    Pager.prototype.clear = function (text) {
        this.pager_element.find(".container").empty();
    };

    Pager.prototype.detach = function(){
        var w = window.open("","_blank");
        $(w.document.head)
        .append(
                $('<link>')
                .attr('rel',"stylesheet")
                .attr('href',"/static/css/notebook.css")
                .attr('type',"text/css")
        )
        .append(
                $('<title>').text("IPython Pager")
        );
        var pager_body = $(w.document.body);
        pager_body.css('overflow','scroll');

        pager_body.append(this.pager_element.clone().children());
        w.document.close();
        this.collapse();

    }

    Pager.prototype.append_text = function (text) {
        this.pager_element.find(".container").append($('<pre/>').html(utils.fixCarriageReturn(utils.fixConsole(text))));
    };


    IPython.Pager = Pager;

    return IPython;

}(IPython));

