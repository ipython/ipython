// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jqueryui',
    'base/js/utils',
], function(IPython, $, utils) {
    "use strict";

    var Pager = function (pager_selector, options) {
        /**
         * Constructor
         *
         * Parameters:
         *  pager_selector: string
         *  options: dictionary
         *      Dictionary of keyword arguments.
         *          events: $(Events) instance
         */
        this.events = options.events;
        this.pager_element = $(pager_selector);
        this.pager_button_area = $('#pager-button-area');    
        this.pager_element.resizable({handles: 'n'});    
        this.expanded = false;
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
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-extlink")
                    )
        );
        this.pager_button_area.append(
            $('<a>').attr('role', "button")
                    .attr('title',"Close the pager")
                    .addClass('ui-button')
                    .click(function(){that.collapse();})
                    .append(
                        $('<span>').addClass("ui-icon ui-icon-close")
                    )
        );
    };


    Pager.prototype.bind_events = function () {
        var that = this;

        this.pager_element.bind('collapse_pager', function (event, extrap) {
            // Animate hiding of the pager.
            that.pager_element.hide((extrap && extrap.duration) ? extrap.duration : 'fast');
        });

        this.pager_element.bind('expand_pager', function (event, extrap) {
            // Clear the pager's height attr if it's set.  This allows the
            // pager to size itself according to its contents.
            that.pager_element.height('initial');

            // Animate the showing of the pager
            var time = (extrap && extrap.duration) ? extrap.duration : 'fast';
            that.pager_element.show(time, function() {
                // Explicitly set pager height once the pager has shown itself.
                // This allows the pager-contents div to use percentage sizing.
                that.pager_element.height(that.pager_element.height());
            });
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
            this.pager_element.trigger('collapse_pager', extrap);
        }
    };


    Pager.prototype.expand = function (extrap) {
        if (this.expanded !== true) {
            this.expanded = true;
            this.pager_element.trigger('expand_pager', extrap);
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
        /**
         * The only user content injected with this HTML call is escaped by
         * the fixConsole() method.
         */
        this.pager_element.find(".container").append($('<pre/>').html(utils.fixCarriageReturn(utils.fixConsole(text))));
    };

    // Backwards compatability.
    IPython.Pager = Pager;

    return {'Pager': Pager};
});
