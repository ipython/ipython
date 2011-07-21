
//============================================================================
// Cell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var SaveWidget = function (selector) {
        this.element = $(selector);
        this.create_element();
        if (this.element !== undefined) {
            this.element.data("cell", this);
            this.bind_events();
        }
    };


    SaveWidget.prototype.bind_events = function () {
        var that = this;
    };


    // Subclasses must implement create_element.
    SaveWidget.prototype.create_element = function () {
        this.element.
            append($('textarea')).
            append($('<button>Save</button>').button());
    };

    IPython.SaveWidget = SaveWidget;

    return IPython;

}(IPython));

