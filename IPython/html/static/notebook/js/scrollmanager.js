// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.
define([], function(){
    "use strict";

    var ScrollManager = function (notebook) {
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
        }
    };

    ScrollManager.prototype.scroll_to = function(destination) {
        // Scroll to an element in the notebook.
        $('#notebook').animate({'scrollTop': $(destination).offset().top + $('#notebook').scrollTop() - $('#notebook').offset().top}, this.animation_speed);
    };

    ScrollManager.prototype.scroll_some = function(pages) {
        // Scroll up or down a given number of pages.
        $('#notebook').animate({'scrollTop': $('#notebook').scrollTop() + pages * $('#notebook').height()}, this.animation_speed);
    };

    // For convinience, add the ScrollManager class to the global namespace
    IPython.ScrollManager = ScrollManager;
    // Return naemspace for require.js loads
    return ScrollManager;

});
