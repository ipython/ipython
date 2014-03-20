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
    content: "Click here to change the filename for this notebook."
  }, {
    element: "#checkpoint_status",
    title: "Checkpoint Status",
    placement: 'bottom',
    content: "Information about the last time this notebook was saved."
  }, {
    element: $("#menus").parent(),
    placement: 'bottom',
    backdrop: true,
    title: "Notebook Menubar",
    content: "The menubar has menus for actions on the notebook, its cells, and the kernel it communicates with."
  }, {
    element: "#maintoolbar",
    placement: 'bottom',
    backdrop: true,
    title: "Notebook Toolbar",
    content: "The toolbar has buttons for the most common actions. Hover your mouse over each button for more information."
  }, {
    element: "#modal_indicator",
    title: "Mode Indicator",
    placement: 'bottom',
    content: "The Notebook has two modes: Edit Mode and Command Mode. In this area, an indicator can appear to tell you which mode you are in.",
    onShow: function(tour) { command_icon_hack(); }
  }, {
    element: "#modal_indicator",
    title: "Command Mode",
    placement: 'bottom',
    onShow: function(tour) { IPython.notebook.command_mode(); command_icon_hack(); },
    onNext: function(tour) { edit_mode(); },
    content: "Right now you are in Command Mode, and many keyboard shortcuts are available. In this mode, no icon is displayed in the indicator area."
  }, {
    element: "#modal_indicator",
    title: "Edit Mode",
    placement: 'bottom',
    onShow: function(tour) { edit_mode(); },
    content: "Pressing <code>Enter</code> or clicking in the input text area of the cell switches to Edit Mode."
  }, {
    element: '.selected',
    title: "Edit Mode",
    placement: 'bottom',
    onShow: function(tour) { edit_mode(); },
    content: "Notice that the border around the currently active cell changed color. Typing will insert text into the currently active cell."
  }, {
    element: '.selected',
    title: "Back to Command Mode",
    placement: 'bottom',
    onShow: function(tour) { IPython.notebook.command_mode(); },
    content: "Pressing <code>Esc</code> or clicking outside of the input text area takes you back to Command Mode."
  }, {
    element: '#keyboard_shortcuts',
    title: "Keyboard Shortcuts",
    placement: 'bottom',
    onShow: function(tour) { $('#help_menu').parent().addClass('open'); },
    onHide: function(tour) { $('#help_menu').parent().removeClass('open'); },
    content: "You can click here to get a list of all of the keyboard shortcuts."
  }, {
    element: "#kernel_indicator",
    title: "Kernel Indicator",
    placement: 'bottom',
    onShow: function(tour) { $([IPython.events]).trigger('status_idle.Kernel');},
    content: "This is the Kernel indicator. It looks like this when the Kernel is idle.",
  }, {
    element: "#kernel_indicator",
    title: "Kernel Indicator",
    placement: 'bottom',
    onShow: function(tour) { $([IPython.events]).trigger('status_busy.Kernel'); },
    content: "The Kernel indicator looks like this when the Kernel is busy.",
  }, {
    element: ".icon-stop",
    placement: 'bottom',
    title: "Interrupting the Kernel",
    onHide: function(tour) { $([IPython.events]).trigger('status_idle.Kernel'); },
    content: "To cancel a computation in progress, you can click here."
  }, {
    element: "#notification_kernel",
    placement: 'bottom',
    onShow: function(tour) { $('.icon-stop').click(); },
    title: "Notification Area",
    content: "Messages in response to user actions (Save, Interrupt, etc) appear here."
  }, {
    element: "#ipython_notebook",
    title: "Fin.",
    placement: 'bottom',
    backdrop: true,
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
    <button class='btn btn-default icon-step-forward pull-right' data-role='next'></button>\
    <button id='tour-pause' class='btn btn-sm btn-default icon-pause' data-resume-text='' data-pause-text='' data-role='pause-resume'></button>\
  </div>\
</div>";

var command_icon_hack =  function() {$('#modal_indicator').css('min-height', 20);}
var toggle_pause_play = function () { $('#tour-pause').toggleClass('icon-pause icon-play'); };
var edit_mode = function() { 
    IPython.notebook.focus_cell(); 
    IPython.notebook.edit_mode();
;}

IPython = (function (IPython) {
 "use strict";

    
    var NotebookTour = function () {
        this.step_duration = 0;
        this.tour_steps = tour_steps ;
        this.tour_steps[0].content = "You can use the left and right arrow keys to go backwards and forwards.";
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
        
    };

    NotebookTour.prototype.start = function () {
        console.log("let's start the tour");
        this.tour.init();
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
