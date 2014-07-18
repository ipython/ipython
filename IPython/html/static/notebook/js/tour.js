// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'bootstraptour',
], function(IPython, $, Tour) {
    "use strict";

    var tour_style = "<div class='popover tour'>\n" +
        "<div class='arrow'></div>\n" +
        "<div style='position:absolute; top:7px; right:7px'>\n" +
            "<button class='btn btn-default btn-sm icon-remove' data-role='end'></button>\n" +
        "</div><h3 class='popover-title'></h3>\n" +
        "<div class='popover-content'></div>\n" +
        "<div class='popover-navigation'>\n" +
            "<button class='btn btn-default icon-step-backward' data-role='prev'></button>\n" +
            "<button class='btn btn-default icon-step-forward pull-right' data-role='next'></button>\n" +
            "<button id='tour-pause' class='btn btn-sm btn-default icon-pause' data-resume-text='' data-pause-text='' data-role='pause-resume'></button>\n" +
        "</div>\n" +
    "</div>";

    var NotebookTour = function (notebook, events) {
        var that = this;
        this.notebook = notebook;
        this.step_duration = 0;
        this.events = events;
        this.tour_steps = [
            { 
                title: "Welcome to the Notebook Tour",
                placement: 'bottom',
                orphan: true,
                content: "You can use the left and right arrow keys to go backwards and forwards.",
            }, {
                element: "#notebook_name",
                title: "Filename",
                placement: 'bottom',
                content: "Click here to change the filename for this notebook."
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
                onShow: function(tour) { that.command_icon_hack(); }
            }, {
                element: "#modal_indicator",
                title: "Command Mode",
                placement: 'bottom',
                onShow: function(tour) { notebook.command_mode(); that.command_icon_hack(); },
                onNext: function(tour) { that.edit_mode(); },
                content: "Right now you are in Command Mode, and many keyboard shortcuts are available. In this mode, no icon is displayed in the indicator area."
            }, {
                element: "#modal_indicator",
                title: "Edit Mode",
                placement: 'bottom',
                onShow: function(tour) { that.edit_mode(); },
                content: "Pressing <code>Enter</code> or clicking in the input text area of the cell switches to Edit Mode."
            }, {
                element: '.selected',
                title: "Edit Mode",
                placement: 'bottom',
                onShow: function(tour) { that.edit_mode(); },
                content: "Notice that the border around the currently active cell changed color. Typing will insert text into the currently active cell."
            }, {
                element: '.selected',
                title: "Back to Command Mode",
                placement: 'bottom',
                onShow: function(tour) { notebook.command_mode(); },
                onHide: function(tour) { $('#help_menu').parent().children('a').click(); },
                content: "Pressing <code>Esc</code> or clicking outside of the input text area takes you back to Command Mode."
            }, {
                element: '#keyboard_shortcuts',
                title: "Keyboard Shortcuts",
                placement: 'bottom',
                onHide: function(tour) { $('#help_menu').parent().children('a').click(); },
                content: "You can click here to get a list of all of the keyboard shortcuts."
            }, {
                element: "#kernel_indicator",
                title: "Kernel Indicator",
                placement: 'bottom',
                onShow: function(tour) { events.trigger('status_idle.Kernel');},
                content: "This is the Kernel indicator. It looks like this when the Kernel is idle.",
            }, {
                element: "#kernel_indicator",
                title: "Kernel Indicator",
                placement: 'bottom',
                onShow: function(tour) { events.trigger('status_busy.Kernel'); },
                content: "The Kernel indicator looks like this when the Kernel is busy.",
            }, {
                element: ".icon-stop",
                placement: 'bottom',
                title: "Interrupting the Kernel",
                onHide: function(tour) { events.trigger('status_idle.Kernel'); },
                content: "To cancel a computation in progress, you can click here."
            }, {
                element: "#notification_kernel",
                placement: 'bottom',
                onShow: function(tour) { $('.icon-stop').click(); },
                title: "Notification Area",
                content: "Messages in response to user actions (Save, Interrupt, etc) appear here."
            }, {
                title: "Fin.",
                placement: 'bottom',
                orphan: true,
                content: "This concludes the IPython Notebook User Interface tour.Tour. Happy hacking!",
            }
        ];

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
            onPause: this.toggle_pause_play,
            onResume: this.toggle_pause_play,
            steps: this.tour_steps,
            template: tour_style,
            orphan: true
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

    NotebookTour.prototype.command_icon_hack =  function() {
        $('#modal_indicator').css('min-height', 20);
    };
    
    NotebookTour.prototype.toggle_pause_play = function () { 
        $('#tour-pause').toggleClass('icon-pause icon-play'); 
    };
    
    NotebookTour.prototype.edit_mode = function() { 
        this.notebook.focus_cell(); 
        this.notebook.edit_mode();
    };

    // For backwards compatability.
    IPython.NotebookTour = NotebookTour;

    return {'Tour': NotebookTour};

});

