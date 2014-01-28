// Test the widget framework.
casper.notebook_test(function () {
    var index;
    
    this.then(function () {
    
        // Check if the WidgetManager class is defined.
        this.test.assert(this.evaluate(function() {
            return IPython.WidgetManager !== undefined; 
        }), 'WidgetManager class is defined');
    });

    index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'print("Success")');
    this.execute_cell_then(index);

    this.wait(500); // Wait for require.js async callbacks to load dependencies.

    this.then(function () {
        // Check if the widget manager has been instantiated.
        this.test.assert(this.evaluate(function() {
            return IPython.notebook.kernel.widget_manager !== undefined; 
        }), 'Notebook widget manager instantiated');
    });

    throttle_index = this.append_cell(
        'import time\n' +
        'textbox = widgets.TextBoxWidget()\n' +
        'display(textbox)\n'+
        'textbox.add_class("my-throttle-textbox")\n' +
        'def handle_change(name, old, new):\n' +
        '    print(len(new))\n' +
        '    time.sleep(0.5)\n' +
        'textbox.on_trait_change(handle_change, "value")\n' +
        'print("Success")');
    this.execute_cell_then(throttle_index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Test throttling cell executed with correct output');

        this.test.assert(this.cell_element_exists(index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(index, 
            '.my-throttle-textbox'), 'Textbox exists.');

        // Send 20 characters
        this.sendKeys('.my-throttle-textbox', '....................');
    });

    this.wait(2000); // Wait for clicks to execute in kernel

    this.then(function(){
        var outputs = this.evaluate(function(i) {
            return IPython.notebook.get_cell(i).output_area.outputs;
        }, {i : throttle_index});

        // Only 4 outputs should have printed, but because of timing, sometimes
        // 5 outputs will print.  All we need to do is verify num outputs <= 5
        // because that is much less than 20.
        this.test.assert(outputs.length <= 5, 'Messages throttled.');

        // We also need to verify that the last state sent was correct.
        var last_state = outputs[outputs.length-1].text;
        this.test.assertEquals(last_state, "20\n", "Last state sent when throttling.");
    });
});
