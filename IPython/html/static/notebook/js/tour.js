//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Tour of IPython Notebok UI (with Bootstrap Tour)
//============================================================================

var tour_steps = [
  { 
    element: $("#ipython_notebook"),
    title: "Welcome to the Notebook Tour",
    placement: 'bottom',
    content: "This tour will take 2 minutes.",
    backdrop: true,
  }, {
    element: "#notebook_name",
    title: "Filename",
    placement: 'bottom',
    content: "You can click here to change the filename for this notebook."
  }, 
          {
    element: "#checkpoint_status",
    title: "Checkpoint status",
    placement: 'bottom',
    content: "Information about the last time this notebook was saved."
  }, {
    element: "#menus",
    placement: 'bottom',
    backdrop: true,
    title: "Notebook Menubar",
    content: "Actions on this notebook, its cells, and the kernel it communicates with."
  }, {
    element: "#notification_kernel",
    placement: 'bottom',
    onShow: function(tour) {  IPython.notification_area.widget_dict.kernel.set_message("sample notification"); },
    onHide: function(tour) {  IPython.notification_area.widget_dict.kernel.set_message("sample notification", 100); },
    title: "Notification area",
    content: "Messages in response to user action (Kernel busy, Interrupt, etc)"
  }, {
    element: "#modal_indicator",
    title: "Mode indicator",
    placement: 'bottom',
    content: "IPython has two modes: Edit Mode and Command Mode. This indicator tells you which mode you are in."
  }, {
    element: "#modal_indicator",
    title: "Mode indicator",
    placement: 'bottom',
    content: "Right now you are in Command mode, and many keyboard shortcuts are available."
  }, {
    element: "#modal_indicator",
    title: "Edit Mode",
    placement: 'bottom',
    onShow: function(tour) { IPython.notebook.edit_mode(); },
    content: "By pressing Enter or clicking in the input area of cell, a we switched to Edit Mode."
  }, {    
    element: "#modal_indicator",
    title: "Edit Mode",
    placement: 'bottom',
    content: "Regular typing will go into the currently active cell."
  }, {
    element: '.selected',
    title: "Edit Mode",
    placement: 'bottom',
    content: "Notice that the border around the currently active cell changed color."
  }, {
    element: '.selected',
    title: "Edit Mode",
    placement: 'bottom',
    onHide: function(tour) { IPython.notebook.command_mode(); },
    content: "Typing in edit mode"
  }, {
    element: '.selected',
    title: "back to Command Mode",
    placement: 'bottom',
    onShow: function(tour) { IPython.notebook.command_mode(); },
    content: "Pressing Esc or clicking outside of the input text area takes you back to command mode."
  }, {
    element: '.selected',
    title: "Command Mode",
    placement: 'bottom',
    onHide: function(tour) { IPython.notebook.command_mode(); },
    content: "This mode exposes many keyboard shortcuts."
  }, {
    element: "#kernel_indicator",
    title: "Kernel indicator",
    placement: 'bottom',
    content: "This is the Kernel indicator. It looks like this when the Kernel is idle.",
  }, {
    element: "#kernel_indicator",
    title: "Kernel Indicator",
    placement: 'bottom',
    onShow: function(tour) { $([IPython.events]).trigger('status_busy.Kernel'); },
    onHide: function(tour) { $([IPython.events]).trigger('status_idle.Kernel');},
    content: "The Kernel indicator looks like this when the Kernel is busy.",
  }, {
    element: "#kernel_indicator",
    title: "Fin.",
    placement: 'bottom',
    onShow: function(tour) { $([IPython.events]).trigger('status_busy.Kernel'); },
    onHide: function(tour) { $([IPython.events]).trigger('status_idle.Kernel');},
    content: "This concludes the IPython Notebook User Interface Tour. Happy hacking!",
  }
];

var tour_style = "<div class='popover tour' style='position:relative'>\
  <div class='arrow'></div>\
    <div style='position:absolute; top:7px; right:7px'>\
        <button class='btn btn-sm icon-remove' data-role='end'></button></div>\
  <h3 class='popover-title'></h3>\
  <div class='popover-content'></div>\
  <div class='popover-navigation'>\
    <button class='btn btn-default icon-step-backward' data-role='prev'></button>\
    <button class='btn btn-default icon-step-forward' data-role='next'></button>\
    <button id='tour-pause' class='btn btn-sm btn-default icon-pause' data-resume-text='' data-pause-text='' data-role='pause-resume'></button>\
  </div>\
</div>"

var toggle_pause_play = function () { $('#tour-pause').toggleClass('icon-pause icon-play'); }

IPython = (function (IPython) {
 "use strict";

    
    var NotebookTour = function () {
        this.step_duration = 5000;
        this.tour_steps = tour_steps ;
        this.tour_steps[0].content = "This tour will take " + this.step_duration * tour_steps.length / 1000 + " seconds";
        this.tour = new Tour({
            //orphan: true,
            storage: false, // start tour from beginning every time
            //element: $("#ipython_notebook"),
            debug: true,
            reflex: true, // click on element to continue tour
            //backdrop: true, // show dark behind popover
            animation: false,
            duration: this.step_duration,
            onStart: function() { console.log('tour started'); },
            // TODO: remove the onPause/onResume logic once pi's patch has been
            // merged upstream to make this work via data-resume-class and 
            // data-resume-text attributes.
            onPause: toggle_pause_play,
            onResume: toggle_pause_play,
            steps: this.tour_steps,
            template: tour_style
        });
        this.tour.init();
    };

    NotebookTour.prototype.start = function () {
        console.log("let's start the tour");
        this.tour.start();
        if (this.tour.ended())
        {
            this.tour.restart();
        }
    };

    // Set module variables
    IPython.NotebookTour = NotebookTour;

    return IPython;

}(IPython));
