// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jqueryui',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";

    var Pager = function (pager_selector, pager_splitter_selector, options) {
        // Constructor
        //
        // Parameters:
        //  pager_selector: string
        //  pager_splitter_selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance
        //          layout_manager: LayoutManager instance
        this.events = options.events;
        this.pager_element = $(pager_selector);
        this.pager_button_area = $('#pager_button_area');
        var that = this;
        this.percentage_height = 0.40;
        options.layout_manager.pager = this;
        this.pager_splitter_element = $(pager_splitter_selector)
            .draggable({
                        containment: 'window',
                        axis:'y',
                        helper: null ,
                        drag: function(event, ui) {
                            // recalculate the amount of space the pager should take
                            var pheight = ($(document.body).height()-event.clientY-4);
                            var downprct = pheight/options.layout_manager.app_height();
                                downprct = Math.min(0.9, downprct);
                            if (downprct < 0.1) {
                                that.percentage_height = 0.1;
                                that.collapse({'duration':0});
                            } else if (downprct > 0.2) {
                                that.percentage_height = downprct;
                                that.expand({'duration':0});
                            }
                            options.layout_manager.do_resize();
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
                    .click(function(){that.detach();})
                    .attr('style','position: absolute; right: 20px;')
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-extlink")
                    )
        );
        this.pager_button_area.append(
            $('<a>').attr('role', "button")
                    .attr('title',"Close the pager")
                    .addClass('ui-button')
                    .click(function(){that.collapse();})
                    .attr('style','position: absolute; right: 5px;')
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-close")
                    )
        );
    };

    Pager.prototype.style = function () {
        this.pager_splitter_element.addClass('ui-widget ui-state-default');
        this.pager_splitter_element.attr('title', 'Click to Show/Hide pager area, drag to Resize');
    };


    Pager.prototype.bind_events = function () {
        var that = this;

        this.pager_element.bind('collapse_pager', function (event, extrap) {
            var time = 'fast';
            if (extrap && extrap.duration) {
                time = extrap.duration;
            }
            that.pager_element.hide(time);
        });

        this.pager_element.bind('expand_pager', function (event, extrap) {
            var time = 'fast';
            if (extrap && extrap.duration) {
                time = extrap.duration;
            }
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

        this.events.on('open_with_text.Pager', function (event, payload) {
            // FIXME: support other mime types
            if (payload.data['text/plain'] && payload.data['text/plain'] !== "") {
                that.clear();
                that.expand();
                that.append_text(payload.data['text/plain']);
            }
        });
    };


    Pager.prototype.collapse = function (extrap) {
        if (this.expanded === true) {
            this.expanded = false;
            this.pager_element.add($('div#notebook')).trigger('collapse_pager', extrap);
        }
    };


    Pager.prototype.expand = function (extrap) {
        if (this.expanded !== true) {
            this.expanded = true;
            this.pager_element.add($('div#notebook')).trigger('expand_pager', extrap);
        }
    };


    Pager.prototype.toggle = function () {
        if (this.expanded === true) {
            this.collapse();
        } else {
            this.expand();
        }
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
    };

    Pager.prototype.append_text = function (text) {
        // The only user content injected with this HTML call is escaped by
        // the fixConsole() method.
        this.pager_element.find(".container").append($('<pre/>').html(utils.fixCarriageReturn(utils.fixConsole(text))));
    };

    // Backwards compatability.
    IPython.Pager = Pager;

    return {'Pager': Pager};
});
