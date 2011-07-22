
//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    // Base PanelSection class

    var PanelSection = function (selector) {
        this.selector = selector;
        if (this.selector !== undefined) {
            this.element = $(selector);
            this.header = this.element.find('h3.section_header');
            this.content = this.element.find('div.section_content');
            this.style();
            this.bind_events();
        }
        this.expanded = true;
    };


    PanelSection.prototype.style = function () {
        this.header.addClass('ui-widget ui-state-default');
        this.content.addClass('ui-widget section_content');
    };


    PanelSection.prototype.bind_events = function () {
        var that = this;
        this.header.click(function () {
            that.toggle();
        });
        this.header.hover(function () {
            that.header.toggleClass('ui-state-hover');
        });
    };


    PanelSection.prototype.expand = function () {
        if (!this.expanded) {
            this.content.slideDown('fast');
            this.expanded = true;
        };
    };


    PanelSection.prototype.collapse = function () {
        if (this.expanded) {
            this.content.slideUp('fast');
            this.expanded = false;
        };
    };


    PanelSection.prototype.toggle = function () {
        if (this.expanded === true) {
            this.collapse();
        } else {
            this.expand();
        };
    };


    PanelSection.prototype.create_children = function () {};


    // NotebookSection

    var NotebookSection = function () {
        PanelSection.apply(this, arguments);
    };


    NotebookSection.prototype = new PanelSection();


    NotebookSection.prototype.style = function () {
        PanelSection.prototype.style.apply(this);
        this.content.addClass('ui-helper-clearfix');
        this.content.find('div.section_row').addClass('ui-helper-clearfix');
        this.content.find('#new_open').buttonset();
    };


    NotebookSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
        this.content.find('#new_notebook').click(function () {
            alert('Not Implemented');
        });
        this.content.find('#open_notebook').click(function () {
            alert('Not Implemented');
        });
    };


    // CellSection

    var CellSection = function () {
        PanelSection.apply(this, arguments);
    };


    CellSection.prototype = new PanelSection();


    CellSection.prototype.style = function () {
        PanelSection.prototype.style.apply(this);
        this.content.addClass('ui-helper-clearfix');
        this.content.find('div.section_row').addClass('ui-helper-clearfix');
        this.content.find('#delete_cell').button();
        this.content.find('#insert').buttonset();
        this.content.find('#move').buttonset();
        this.content.find('#cell_type').buttonset();
        this.content.find('#toggle_output').buttonset();
        this.content.find('#run_cells').buttonset();
    };


    CellSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
        this.content.find('#collapse_cell').click(function () {
            IPython.notebook.collapse();
        });
        this.content.find('#expand_cell').click(function () {
            IPython.notebook.expand();
        });
        this.content.find('#delete_cell').click(function () {
            IPython.notebook.delete_cell();
        });
        this.content.find('#insert_cell_above').click(function () {
            IPython.notebook.insert_code_cell_before();
        });
        this.content.find('#insert_cell_below').click(function () {
            IPython.notebook.insert_code_cell_after();
        });
        this.content.find('#move_cell_up').click(function () {
            IPython.notebook.move_cell_up();
        });
        this.content.find('#move_cell_down').click(function () {
            IPython.notebook.move_cell_down();
        });
        this.content.find('#to_code').click(function () {
            IPython.notebook.text_to_code();
        });
        this.content.find('#to_text').click(function () {
            IPython.notebook.code_to_text();
        });
        this.content.find('#run_selected_cell').click(function () {
            alert("Not Implemented");
        });
        this.content.find('#run_all_cells').click(function () {
            alert("Not Implemented");
        });
    };


    // KernelSection

    var KernelSection = function () {
        PanelSection.apply(this, arguments);
    };


    KernelSection.prototype = new PanelSection();


    KernelSection.prototype.style = function () {
        PanelSection.prototype.style.apply(this);
        this.content.addClass('ui-helper-clearfix');
        this.content.find('div.section_row').addClass('ui-helper-clearfix');
        this.content.find('#int_restart').buttonset();
    };


    KernelSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
        this.content.find('#restart_kernel').click(function () {
            IPython.notebook.kernel.restart();
        });
        this.content.find('#int_kernel').click(function () {
            IPython.notebook.kernel.interrupt();
        });
    };


    // HelpSection

    var HelpSection = function () {
        PanelSection.apply(this, arguments);
    };


    HelpSection.prototype = new PanelSection();


    HelpSection.prototype.style = function () {
        PanelSection.prototype.style.apply(this);
        PanelSection.prototype.style.apply(this);
        this.content.addClass('ui-helper-clearfix');
        this.content.find('div.section_row').addClass('ui-helper-clearfix');
        this.content.find('#help_buttons0').buttonset();
        this.content.find('#help_buttons1').buttonset();
    };


    HelpSection.prototype.bind_events = function () {
        PanelSection.prototype.bind_events.apply(this);
    };


    // Set module variables

    IPython.PanelSection = PanelSection;
    IPython.NotebookSection = NotebookSection;
    IPython.CellSection = CellSection;
    IPython.KernelSection = KernelSection;
    IPython.HelpSection = HelpSection;

    return IPython;

}(IPython));

