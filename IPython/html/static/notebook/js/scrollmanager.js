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
            that.notebook.scrollmanager = manager;
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
        var cell_count = this.notebook.ncells();
        var first_cell_top = this.notebook.get_cell(0).element.offset().top;
        var last_cell_top = this.notebook.get_cell(cell_count-1).element.offset().top;
        var avg_cell_height = (last_cell_top - first_cell_top) / cell_count;
        var notebook = $('#notebook');
        var i = Math.ceil(notebook.scrollTop() / avg_cell_height);
        i = Math.min(Math.max(i , 0), cell_count - 1);

        while (this.notebook.get_cell(i).element.offset().top - first_cell_top < notebook.scrollTop() && i < cell_count - 1) {
            i += 1;
        } 

        while (this.notebook.get_cell(i).element.offset().top - first_cell_top > notebook.scrollTop() - 50 && i >= 0) {
            i -= 1;
        } 
        return Math.min(i + 1, cell_count - 1);
    };


    var TargetScrollManager = function(notebook) {
        // Public constructor.
        ScrollManager.apply(this, [notebook]);
    };
    TargetScrollManager.prototype = new ScrollManager();

    TargetScrollManager.prototype.is_target = function (index) {
        return false;
    };

    TargetScrollManager.prototype.scroll = function (delta) {
        // Scroll the document.
        //
        // Parameters
        // ----------
        // delta: integer
        //  direction to scroll the document.  Positive is downwards.

        // Try to scroll to the next slide.
        var cell_count = this.notebook.ncells();
        var selected_index = this.get_first_visible_cell() + delta;
        while (0 <= selected_index && selected_index < cell_count && !this.is_target(selected_index)) {
            selected_index += delta;
        }

        if (selected_index < 0 || cell_count <= selected_index) {
            return ScrollManager.prototype.scroll.apply(this, [delta]);
        } else {
            this.scroll_to(this.notebook.get_cell(selected_index).element);
            
            // Cancel browser keyboard scroll.
            return false;
        }
    };


    var SlideScrollManager = function(notebook) {
        // Public constructor.
        TargetScrollManager.apply(this, [notebook]);
    };
    SlideScrollManager.prototype = new TargetScrollManager();

    SlideScrollManager.prototype.is_target = function (index) {
        var cell = this.notebook.get_cell(index);
        return cell.metadata && cell.metadata.slideshow && 
            cell.metadata.slideshow.slide_type && 
            cell.metadata.slideshow.slide_type === "slide";
    };


    var HeadingScrollManager = function(notebook, heading_level) {
        // Public constructor.
        TargetScrollManager.apply(this, [notebook]);
        this._level = heading_level;
    };
    HeadingScrollManager.prototype = new TargetScrollManager();

    HeadingScrollManager.prototype.is_target = function (index) {
        var cell = this.notebook.get_cell(index);
        return cell.cell_type === "heading" && cell.level == this._level;
    };


    // Return naemspace for require.js loads
    return {
        'ScrollSelector': ScrollSelector,
        'ScrollManager': ScrollManager,
        'SlideScrollManager': SlideScrollManager,
        'HeadingScrollManager': HeadingScrollManager,
        'TargetScrollManager': TargetScrollManager
    };
});
