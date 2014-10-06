// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'notebook/js/celltoolbar',
    'bootstraptags',
], function($, celltoolbar, bootstraptags) {
    "use strict";

    var get_suggestions = function() {
        // Get a list of suggestions to use in the tags toolbar.
        var suggestions = [];
        var cells = IPython.notebook.get_cells();
        for (var i = 0; i < cells.length; i++) {
            if (cells[i].metadata.tags) {
                suggestions = $.merge(suggestions, cells[i].metadata.tags);
            }
        }

        if (IPython.notebook.tag_suggestions) {
            if (IPython.notebook.tag_suggestions instanceof Function) {
                suggestions = $.merge(suggestions, IPython.notebook.tag_suggestions.apply(this, []));
            } else {
                suggestions = $.merge(suggestions, IPython.notebook.tag_suggestions);
            }
        }
        return suggestions;
    };

    var toolbar_tag_ui_generator = function(keyboard_manager, setter, getter){
        // Generate a tags cell toolbar control.
        return function(div, cell, celltoolbar) {
            var $button_container = $(div).addClass('box-flex1');
            var $tag_list = $('<div/>')
                .addClass('tag-list');
            $button_container.append($tag_list);

            var tags = $tag_list.tags({
                tagData: getter(cell),
                suggestions: get_suggestions(),
                caseInsensitive: true
            });
            $tag_list.data('tags', tags);
            $tag_list.click(function(){
                tags.renderTags();
            })
            $tag_list.keyup(function(){
                setter(cell, tags.getTags());
            });
            $tag_list.find('input').width('100%');
            keyboard_manager.register_events($tag_list);
        };
    };

    var register = function (notebook, keyboard_manager) {
        // Register the cell tagging toolbar.

        // Change the tag template so font-awesome icons are used.
        bootstraptags.Templates = bootstraptags.Templates || {};
        bootstraptags.Templates['3'] = bootstraptags.Templates['3'] || {};
        bootstraptags.Templates['3'].tag = function(options) {
            options = options || {};
            return "<div class='tag label " + options.tagClass + " " + options.tagSize + "' " + (options.isPopover ? "rel='popover'" : "") + ">    <span>" + Tags.Helpers.addPadding(options.tag, 2, options.isReadOnly) + "</span>    " + (options.isReadOnly ? "" : "<a><i style='color: white;' class='remove fa fa-times' /></a>") + "  </div>";
        };

        // Register the cell tagging toolbar.
        var tags = toolbar_tag_ui_generator(keyboard_manager, 
            function(cell, tags){ // Setter
                cell.metadata.tags = tags;
                console.log(cell, tags);
                
                var $tag_inputs = $('.celltoolbar .bootstrap-tags');
                var suggestions = get_suggestions();
                for (var i =0; i < $tag_inputs.length; i++) {
                    $($tag_inputs[i]).data('tags').suggestions = suggestions;
                }
            },
            function(cell){ // Getter
                return cell.metadata.tags;
            });
        celltoolbar.CellToolbar.register_callback('default.tags', tags);
        celltoolbar.CellToolbar.register_preset('Cell tags', ['default.tags'], notebook);
        console.log('Cell tags extension loaded.');
    };
    return {'register': register};
});
