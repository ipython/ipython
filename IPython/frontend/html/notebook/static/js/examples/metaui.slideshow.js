//----------------------------------------------------------------------------
//  Copyright (C) 2012  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// MetaUI Example
//============================================================================

/**
 * Example Use for the MetaUI library
 * add the following to your custom.js to load
 * metadata UI for slideshow
 *
 * ```
 * $.getScript('/static/js/examples/metaui.slideshow.js');
 * ```
 */
 // IIFE without asignement, we don't modifiy the IPython namespace
(function (IPython) {
    "use strict";

    var MetaUI = IPython.MetaUI;
    var slideshow_preset = [];

    var hslide = MetaUI.utils.checkbox_ui_generator('New Section',
            function(md,value){
                if (md.slideshow == undefined){md.slideshow = {}}
                return md.slideshow.new_section = value},
            function(md){ var ns = md.slideshow;
                return (ns == undefined)? undefined: ns.new_section});

    var vslide = MetaUI.utils.checkbox_ui_generator('New Subsection',
            function(md,value){
                if (md.slideshow == undefined){md.slideshow = {}}
                return md.slideshow.new_subsection = value},
            function(md){ var ns = md.slideshow;
                return (ns == undefined)? undefined: ns.new_subsection});

    var fragment = MetaUI.utils.checkbox_ui_generator('New Fragment',
            function(md,value){
                if (md.slideshow == undefined){md.slideshow = {}}
                return md.slideshow.new_fragment = value},
            function(md){ var ns = md.slideshow;
                return (ns == undefined)? undefined: ns.new_fragment});


    MetaUI.register_callback('slideshow.hslide',hslide);
    MetaUI.register_callback('slideshow.vslide',vslide);
    MetaUI.register_callback('slideshow.fragment',fragment);

    slideshow_preset.push('slideshow.fragment');
    slideshow_preset.push('slideshow.vslide');
    slideshow_preset.push('slideshow.hslide');


    MetaUI.register_preset('slideshow',slideshow_preset);
    MetaUI.set_preset('slideshow');
    console.log('Slideshow extension for metadata editting loaded.');

}(IPython));
