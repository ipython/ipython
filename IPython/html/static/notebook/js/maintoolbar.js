// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'notebook/js/toolbar',
    'notebook/js/celltoolbar',
], function(IPython, $, toolbar, celltoolbar) {
    "use strict";

    var MainToolBar = function (selector, options) {
        // Constructor
        //
        // Parameters:
        //  selector: string
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance
        //          notebook: Notebook instance
        toolbar.ToolBar.apply(this, arguments);
        this.events = options.events;
        this.notebook = options.notebook;
        this.construct();
        this.add_celltype_list();
        this.add_celltoolbar_list();
        this.bind_events();
    };

    MainToolBar.prototype = new toolbar.ToolBar();

    MainToolBar.prototype.construct = function () {
        var that = this;
        this.add_buttons_group([
                {
                    id : 'save_b',
                    label : 'Save and Checkpoint',
                    icon : 'fa-save',
                    callback : function () {
                        that.notebook.save_checkpoint();
                        }
                }
            ]);

        this.add_buttons_group([
                {
                    id : 'insert_below_b',
                    label : 'Insert Cell Below',
                    icon : 'fa-plus',
                    callback : function () {
                        that.notebook.insert_cell_below('code');
                        that.notebook.select_next();
                        that.notebook.focus_cell();
                        }
                }
            ],'insert_above_below');

        this.add_buttons_group([
                {
                    id : 'cut_b',
                    label : 'Cut Cell',
                    icon : 'fa-cut',
                    callback : function () {
                        that.notebook.cut_cell();
                        }
                },
                {
                    id : 'copy_b',
                    label : 'Copy Cell',
                    icon : 'fa-copy',
                    callback : function () {
                        that.notebook.copy_cell();
                        }
                },
                {
                    id : 'paste_b',
                    label : 'Paste Cell Below',
                    icon : 'fa-paste',
                    callback : function () {
                        that.notebook.paste_cell_below();
                        }
                }
            ],'cut_copy_paste');

        this.add_buttons_group([
                {
                    id : 'move_up_b',
                    label : 'Move Cell Up',
                    icon : 'fa-arrow-up',
                    callback : function () {
                        that.notebook.move_cell_up();
                        }
                },
                {
                    id : 'move_down_b',
                    label : 'Move Cell Down',
                    icon : 'fa-arrow-down',
                    callback : function () {
                        that.notebook.move_cell_down();
                        }
                }
            ],'move_up_down');
        

        this.add_buttons_group([
                {
                    id : 'run_b',
                    label : 'Run Cell',
                    icon : 'fa-play',
                    callback : function () {
                        // emulate default shift-enter behavior
                        that.notebook.execute_cell_and_select_below();
                    }
                },
                {
                    id : 'interrupt_b',
                    label : 'Interrupt',
                    icon : 'fa-stop',
                    callback : function () {
                        that.notebook.kernel.interrupt();
                        }
                },
                {
                    id : 'repeat_b',
                    label : 'Restart Kernel',
                    icon : 'fa-repeat',
                    callback : function () {
                        that.notebook.restart_kernel();
                        }
                }
            ],'run_int');

        this.add_buttons_group([{
            id : 'filter_toggle',
            label : 'Filter based on cell tags',
            icon : 'fa-filter',
            callback : $.proxy(this._handle_filter_click, this)}]);
    };
    
    MainToolBar.prototype._handle_filter_click = function (e) {
        // Handles when the filter button is clicked.

        var $filter_button = $(e.currentTarget);
        var $filter_text;

        // If a filter textbox already exists, remove the textbox.
        if ($filter_button.data('filter_text')) {

            // Animate the textbox 'closing', and then remove it from the DOM.
            $filter_text = $filter_button.data('filter_text')
            var that = this;
            $filter_text.animate({width: 0}, 200, 
                'swing', function() {
                that._handle_filter();
                $filter_text.remove();
            });
            $filter_button.data('filter_text', false);
            
        // A filter textbox doesn't exist yet.  Create a filter textbox here.
        } else {
            $filter_text = $('<input/>')
                .attr('type', 'text')
                .attr('placeholder', 'Tag filter expression...')
                .width(0)
                .addClass('form-control input-sm');
            $filter_button.data('filter_text', $filter_text);
            $filter_button.after($filter_text);
            
            // Prevent notebook events from firing when the user types in the 
            // filter textbox.
            this.notebook.keyboard_manager.register_events($filter_text);

            // Make sure the button group has a css class that we can style.
            $filter_button.parent().addClass('filter-control');

            // Animate the textbox's display.
            $filter_text.animate({width: 200}, 200, 'swing');

            // Handle when the filter is changed.
            $filter_text.on('change', $.proxy(this._handle_filter, this));
        }
    };

    MainToolBar.prototype._handle_filter = function(e) {
        // Handle when the user sets a filter.

        // If the event object `e` exists, assume this method was fired as the
        // result of an event and get the value of the filter from the value of
        // the object that caused the event to fire.  Otherwise, assume the 
        // filter is empty.
        var filter;
        if (e) {
            var $filter_text = $(e.currentTarget);
            filter = $filter_text.val();
        } else {
            filter = '';
        }
        
        // Evaluate the filter for each cell.
        var cells = IPython.notebook.get_cells();
        for (var i = 0; i < cells.length; i++) {
            var tags = $.merge([], cells[i].metadata.tags);
            // Add the cell type as a tag that can be filtered by.
            tags.push(cells[i].cell_type);
            cells[i].element.css('display', this._eval_expression(tags, filter) ? '' : 'none');
        }
    };

    MainToolBar.prototype._eval_expression = function(truths, expression) {
        // Evaluate a simple expression given a list of truths.
        //
        // Parameters
        // ----------
        // truths: list(of string)
        //      Each value in this list is treated as a `true` boolean when the
        //      expression is evaluated.
        // expression: string
        //      An expression.  `not`, `and`, `or`, and parenthesis are 
        //      supported.  `true` and `false` are keywords of the evaluator.
        //
        // Returns
        // -------
        // boolean result of the expression.

        // Find the opening parenthesis first, if it exists.  Then walk until
        // the matching close parenthesis is found.  Make sure that 
        var parenthesis_start = expression.indexOf('(');
        var parenthesis_end = expression.lastIndexOf(')');
        if (parenthesis_start != -1) {
            var depth = 0;
            for (var i = parenthesis_start + 1; i < expression.length; i++) {
                if (expression[i] == '(') { depth++; }
                if (expression[i] == ')') { depth--; }
                if (depth == -1) {
                    parenthesis_end = i;
                    break;
                }
            }
        }

        // Check the parenthesis indicies to determine whether or not the 
        // expression should be broken into pieces.  Also validate that the
        // parenthesis are properly balanced.
        if (parenthesis_start != -1 && parenthesis_end != -1) {
            if (parenthesis_end > parenthesis_start) {

                // Evaluate the sub-expression in the parenthesis first.  Then
                // re-embed the sub-expression's results into the location in
                // the expression that it existed in initially.
                var start = expression.substring(0, parenthesis_start-1);
                var mid_results = eval_filter(truths, expression.substring(parenthesis_start+1, parenthesis_end-1));
                var end = expression.substring(parenthesis_end+1);
                expression = start + ' ' + mid_results.toString().toLowerCase() && end;
            } else {
                console.log(') found before (');
            }
        } else if (parenthesis_start != -1 || parenthesis_end != -1) {
            console.log('unbalanced parenthesis');
        }
        
        // If the expression is empty, return true.
        expression = expression.trim();
        if (!expression) {
            return true;
        } else {

            // Evaluation flags.
            var needs_or = false;
            var is_not = false;

            // Evaluate the expression from left to right.
            var parts = expression.split(' ');
            for (var i = 0; i < parts.length; i++) {

                // If an `or` is needed because the preceeding expression 
                // evaluated to false and the `or` cannot be found, return false.
                var part = parts[i].trim().toLowerCase();
                if (part != 'or' && needs_or) {
                    return false;
                }
                
                // Evaluate the current word of the expression.
                if (part == 'and') { 
                } else if (part == 'or') {
                    // An `or` was found.  If the `or` flag is set, reset it
                    // and continue evaluation.  Otherwise, return true since
                    // the preceeding expression evaluated to true.
                    if (needs_or) {
                        needs_or = false;
                    } else {
                        return true;
                    }
                } else if (part == 'not') {
                    // Set the `not` flag.
                    is_not = !is_not;
                } else {
                    var value;
                    if (part == 'false' || part == 'true') {
                        value = (part == 'true');
                    } else {    
                        // Value is a non-keyword.  Check if it exists in the
                        // list of truths.  If it doesn't exist, it's a false.
                        var contains = false;
                        for (var j = 0; j < truths.length; j++) {
                            if (truths[j].toLowerCase() == part) {
                                contains = true;
                                break;
                            }
                        }
                        value = contains;
                    }
                    
                    // Invert the results if the `not` flag is set.
                    if (is_not) {
                        value = !value;
                        is_not = false;
                    }
                    
                    // If the results are false, set the `or` flag to signify
                    // that an `or` is required in order for the expression to
                    // have a possibility of evaluating as true.
                    if (!value) {
                        needs_or = true;
                    }
                }
            }
            
            return !needs_or;
        }
    }

    
    MainToolBar.prototype.add_celltype_list = function () {
        this.element
            .append($('<select/>')
                .attr('id','cell_type')
                .addClass('form-control select-xs')
                .append($('<option/>').attr('value','code').text('Code'))
                .append($('<option/>').attr('value','markdown').text('Markdown'))
                .append($('<option/>').attr('value','raw').text('Raw NBConvert'))
                .append($('<option/>').attr('value','heading1').text('Heading 1'))
                .append($('<option/>').attr('value','heading2').text('Heading 2'))
                .append($('<option/>').attr('value','heading3').text('Heading 3'))
                .append($('<option/>').attr('value','heading4').text('Heading 4'))
                .append($('<option/>').attr('value','heading5').text('Heading 5'))
                .append($('<option/>').attr('value','heading6').text('Heading 6'))
            );
    };

    MainToolBar.prototype.add_celltoolbar_list = function () {
        var label = $('<span/>').addClass("navbar-text").text('Cell Toolbar:');
        var select = $('<select/>')
            .attr('id', 'ctb_select')
            .addClass('form-control select-xs')
            .append($('<option/>').attr('value', '').text('None'));
        this.element.append(label).append(select);
        var that = this;
        select.change(function() {
                var val = $(this).val();
                if (val ==='') {
                    celltoolbar.CellToolbar.global_hide();
                    delete that.notebook.metadata.celltoolbar;
                } else {
                    celltoolbar.CellToolbar.global_show();
                    celltoolbar.CellToolbar.activate_preset(val, that.events);
                    that.notebook.metadata.celltoolbar = val;
                }
            });
        // Setup the currently registered presets.
        var presets = celltoolbar.CellToolbar.list_presets();
        for (var i=0; i<presets.length; i++) {
            var name = presets[i];
            select.append($('<option/>').attr('value', name).text(name));
        }
        // Setup future preset registrations.
        this.events.on('preset_added.CellToolbar', function (event, data) {
            var name = data.name;
            select.append($('<option/>').attr('value', name).text(name));
        });
        // Update select value when a preset is activated.
        this.events.on('preset_activated.CellToolbar', function (event, data) {
            if (select.val() !== data.name)
                select.val(data.name);
        });
    };

    MainToolBar.prototype.bind_events = function () {
        var that = this;
        
        this.element.find('#cell_type').change(function () {
            var cell_type = $(this).val();
            if (cell_type === 'code') {
                that.notebook.to_code();
            } else if (cell_type === 'markdown')  {
                that.notebook.to_markdown();
            } else if (cell_type === 'raw')  {
                that.notebook.to_raw();
            } else if (cell_type === 'heading1')  {
                that.notebook.to_heading(undefined, 1);
            } else if (cell_type === 'heading2')  {
                that.notebook.to_heading(undefined, 2);
            } else if (cell_type === 'heading3')  {
                that.notebook.to_heading(undefined, 3);
            } else if (cell_type === 'heading4')  {
                that.notebook.to_heading(undefined, 4);
            } else if (cell_type === 'heading5')  {
                that.notebook.to_heading(undefined, 5);
            } else if (cell_type === 'heading6')  {
                that.notebook.to_heading(undefined, 6);
            }
        });
        this.events.on('selected_cell_type_changed.Notebook', function (event, data) {
            if (data.cell_type === 'heading') {
                that.element.find('#cell_type').val(data.cell_type+data.level);
            } else {
                that.element.find('#cell_type').val(data.cell_type);
            }
        });
    };

    // Backwards compatability.
    IPython.MainToolBar = MainToolBar;

    return {'MainToolBar': MainToolBar};
});
