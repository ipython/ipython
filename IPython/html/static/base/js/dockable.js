// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
], function($){
    "use strict";

    var _dockables = [];
    var _bring_to_front = function($dockable) {
        // Make the modal top-most, z-ordered about the other modals.
        var max_zindex = 0;
        var index;
        var $el;
        for (index = 0; index < _dockables.length; index++) {
            $el = _dockables[index];
            var zindex = parseInt($el.css('z-index'));
            if (!isNaN(zindex)) {
                max_zindex = Math.max(max_zindex, zindex);
            }
        }
        
        // Start z-index of widget modals at 2000
        max_zindex = Math.max(max_zindex, 2000);
        
        for (index = 0; index < _dockables.length; index++) {
            $el = _dockables[index];
            if (max_zindex == parseInt($el.css('z-index'))) {
                $el.css('z-index', max_zindex - 1);
            }
        }
        $dockable.css('z-index', max_zindex);
    };

    var make_dockable = function($el, drag_selector, on_dock, on_undock, on_drag) {
        $el.docked = true;
        $el.addClass('docked-dockable');
        if (on_dock) { on_dock($el); }                    
        var $previous = $el.prev();
        var $parent = $el.parent();

        $el.click(function() {
            if (!$el.docked) {
                _bring_to_front($el);
            }
        });

        var do_dock = function() {
            dock_button_icon
                .addClass('fa-arrow-up')
                .removeClass('fa-arrow-down');
            $el
                .css('max-width', '')
                .css('max-height', '')
                .css('z-index', '')
                .detach();
            if ($previous.length > 0) {
                $el.insertAfter($previous);
            } else {
                $parent.prepend($el);
            }
            $el
                .removeClass('undocked-dockable')
                .addClass('docked-dockable');
            $el.docked = true;
            if (on_dock) { on_dock($el); }   
        };

        var do_undock = function() {
            dock_button_icon
                .removeClass('fa-arrow-up')
                .addClass('fa-arrow-down');
            $previous = $el.prev();
            $parent = $el.parent();

            var calculate_drag_bounds = function() {
                var padding = Math.ceil(2.0 * (parseFloat($el.css('padding')) + parseFloat($el.css('border-width'))));
                return {
                    left: 0,
                    right: $('body').width() - ($el.width() + padding),
                    top: $('#header').position().top + $('#header').height(),
                    bottom: window.innerHeight - ($el.height() + padding),
                };
            };

            var last_doc_timeout;
            var query_doc;
            var dock_zone;
            var handle_drag = function(event, ui) {
                var bounds = calculate_drag_bounds();

                ui.position.left = Math.max(event.clientX, ui.position.left + $el.width()) - $el.width();
                ui.position.top = Math.max(event.clientY, ui.position.top + $el.height()) - $el.height();

                ui.position.left = Math.min(Math.max(ui.position.left, bounds.left), bounds.right);
                ui.position.top = Math.min(Math.max(ui.position.top, bounds.top), bounds.bottom);

                if ($el.stretched) {
                    $el.stretched = false;
                    $el.removeClass('stretched');
                    $el.width('');
                    $el.height('');
                    $el.css('bottom', '');
                    $el.css('position', 'fixed');
                    $el.resizable('disable').removeClass('ui-state-disabled');
                }
                    
                if (on_drag) { on_drag.apply(this, [event, ui]); }

                if (ui.position.top >= bounds.bottom - 10) {
                    if (!last_doc_timeout) {
                        last_doc_timeout = setTimeout(function() { 
                            last_doc_timeout = undefined;
                            query_doc = true;

                            dock_zone = $('.dock_zone');
                            if (!dock_zone.length) {
                                dock_zone = $('<div />');
                                dock_zone.addClass('dock_zone');
                                dock_zone.hide();
                                dock_zone.height(200);
                                dock_zone.appendTo('body');    
                            }
                            
                            dock_zone.width($('body').width());
                            dock_zone.css('position', 'fixed');
                            dock_zone.css('bottom', 0);
                            dock_zone.css('left', 0);
                            dock_zone.css('background-color', 'black');
                            dock_zone.css('opacity', '0.2');
                            dock_zone.fadeIn(150, 'swing', function() {});
                        }, 350);    
                    }                    
                } else {
                    if (last_doc_timeout) {
                        clearTimeout(last_doc_timeout);
                        last_doc_timeout = undefined;
                    }
                    if (query_doc) {
                        dock_zone.fadeOut(150, 'swing', function() {});
                    }
                    query_doc = undefined;
                }
            };

            $el
                .removeClass('docked-dockable')
                .addClass('undocked-dockable')
                .detach()
                .appendTo($('body'))
                .draggable({
                    handle: drag_selector, 
                    snap: '.modal', 
                    snapMode: 'both',
                    drag: handle_drag,
                    start: function() {
                        _bring_to_front($el);
                        $el.css('max-width', $('body').width() / 2);
                        $el.css('max-height', '');
                    },
                    stop: function() {
                        if (query_doc) {
                            $el.stretched = true;
                            $el.addClass('stretched');
                            $el.height(200);
                            $el.width($('body').width());
                            $el.css('top', '');
                            $el.css('bottom', 0);
                            $el.css('left', 0);
                            $el.css('position', 'absolute');
                            $el.css('max-width', '');
                            $el.css('max-height', '');
                            $el.resizable({handles: 'n'});
                            $el.resizable('enable');
                        }
                        if (last_doc_timeout) {
                            clearTimeout(last_doc_timeout);
                            last_doc_timeout = undefined;
                        }
                        if (dock_zone) {
                            dock_zone.hide();
                        }
                    },
                })
                .css('top', calculate_drag_bounds().top);

            _bring_to_front($el);
            $el.docked = false;
            if (on_undock) { on_undock($el); }
        };

        _dockables.push($el);
        var dock_button_icon = $('<span />')
                .attr('aria-hidden', 'true')
                .addClass('fa fa-arrow-up docking-button');
        var dock_button = $('<button />')
            .attr('type', 'button')
            .addClass('close')
            .css('float', 'right')
            .click(function() {
                $el.docked = !$el.docked;
                if ($el.docked) {
                    do_dock();                 
                } else {
                    do_undock();
                }
            })
            .append(dock_button_icon)
            .appendTo($el);

        $el.dock_button = dock_button;
        $el.dock = do_dock;
        $el.undock = do_undock;
    };
    
    return {make_dockable: make_dockable};
});