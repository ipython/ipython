// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.
define(['jquery'], function($){
    "use strict";

    var ScrollSelector = function(element, notebook) {
        // Public constructor.
        this.notebook = notebook;
        $('<span />')
            .addClass('nabar-text')
            .text('Scrolling Mode:')
            .appendTo(element);
        this._combo = $('<select />')
            .addClass('form-control select-xs')
            .appendTo(element);

        // Redirect class level manager registration to this instance.
        this._registered = {};
        ScrollSelector.register = $.proxy(this.register, this);

        // Register cached managers.
        for (var i =0; i < ScrollSelector.registered.length; i++) {
            this.register.apply(this, ScrollSelector.registered[i]);
        }

        // Listen for scroll manager change, apply it to the notebook.
        var that = this;
        this._combo.change(function(){
            var manager = that._registered[$(this).find("option:selected").val()];
            that.notebook.ScrollSelector = manager;
        });
    };

    // Cache scroll managers registered before the construction of a scroll 
    // manager.
    ScrollSelector.registered = [];
    ScrollSelector.register = function(name, manager) {
        ScrollSelector.registered.push(arguments);
    };
    ScrollSelector.prototype.register = function(name, manager) {
        this._registered[name] = manager;
        this._combo.append($('<option />')
            .val(name)
            .text(name));
    };


    var ScrollManager = function(notebook) {
        // Public constructor.
        this.notebook = notebook;
        this.animation_speed = 250; //ms
    };

    ScrollManager.prototype.scroll = function (delta) {
        // Scroll the document.
        //
        // Parameters
        // ----------
        // delta: integer
        //  direction to scroll the document.  Positive is downwards.
        this.scroll_some(delta);
        return false;
    };

    ScrollManager.prototype.scroll_to = function(destination) {
        // Scroll to an element in the notebook.
        $('#notebook').animate({'scrollTop': $(destination).offset().top + $('#notebook').scrollTop() - $('#notebook').offset().top}, this.animation_speed);
    };

    ScrollManager.prototype.scroll_some = function(pages) {
        // Scroll up or down a given number of pages.
        $('#notebook').animate({'scrollTop': $('#notebook').scrollTop() + pages * $('#notebook').height()}, this.animation_speed);
    };

    ScrollManager.prototype.get_first_visible_cell = function() {
        // Gets the index of the first visible cell in the document.

        // First, attempt to be smart by guessing the index of the cell we are
        // scrolled to.  Then, walk from there up or down until the right cell 
        // is found.  To guess the index, get the top of the last cell, and
        // divide that by the number of cells to get an average cell height.  
        // Then divide the scroll height by the average cell height.
        var cell_count = that.notebook.ncells();
        var first_cell_top = that.notebook.get_cell(0).element.offset.top();
        var last_cell_top = that.notebook.get_cell(cell_count-1).element.offset.top();
        var avg_cell_height = (last_cell_top - first_cell_top) / cell_count;
        var $notebook = $('#notebook').scrollTop();
        var i = Math.ceil($notebook.scrollTop() / avg_cell_height);
        i = min(max(i , 0), cell_count - 1);

        while (that.notebook.get_cell(i).element.offset.top() - first_cell_top < $notebook.scrollTop() && i < cell_count - 1) {
            i += 1;
        } 

        while (that.notebook.get_cell(i).element.offset.top() - first_cell_top > $notebook.scrollTop() && i >= 0) {
            i -= 1;
        } 
        return min(i + 1, cell_count - 1);
    };


    var HeadingScrollManager = function(notebook, heading_level) {
        // Public constructor.
    };


    var SlideScrollManager = function(notebook) {
        // Public constructor.
    };

/*// Scroll the document.
        //
        // Parameters
        // ----------
        // delta: integer
        //  direction to scroll the document.  Positive is downwards.

        // If one or more slides exist, scroll to the slide.
        var $slide_cells = $('.slideshow-slide');
        if ($slide_cells.length > 0) {
            var i, cell;

            // Get the active slide cell index.
            var selected_index = this.notebook.find_cell_index(this.notebook.get_selected_cell());
            var active_slide = -1;
            var cells = this.notebook.get_cells();
            for (i = selected_index; i >= 0; i--) {
                cell = cells[i];
                var ns = cell.metadata.slideshow;
                if (ns && ns.slide_type == 'slide') {
                    active_slide = i;
                    break;
                }
            }
            
            // Translate cell index into slide cell index.
            if (active_slide != -1) {
                for (i = 0; i < $slide_cells.length; i++) {
                    if (cells[active_slide].element[0] == $slide_cells[i]) {
                        active_slide = i;
                        break;
                    }
                } 
            }
        
            // Scroll.
            if (active_slide != -1 || delta > 0) {
                active_slide += delta;
                active_slide = Math.max(0, Math.min($slide_cells.length-1, active_slide));
                
                var cell_element = $slide_cells[active_slide];
                cell = $(cell_element).data('cell');
                this.notebook.select(this.notebook.find_cell_index(cell));
                
                this.scroll_to(cell_element);
                //cell_element.scrollIntoView(true);
            }

            // Cancel browser keyboard scroll.
            return false;
        
        // No slides exist, scroll up or down one page height.  Instead of using
        // the browser's built in method to do this, animate it using jQuery.
        } else {
            this.scroll_some(delta);
            return false;
        }*/

    // Return naemspace for require.js loads
    return {
        'ScrollSelector': ScrollSelector,
        'ScrollManager': ScrollManager,
        'SlideScrollManager': SlideScrollManager,
        'HeadingScrollManager': HeadingScrollManager
    };
});
