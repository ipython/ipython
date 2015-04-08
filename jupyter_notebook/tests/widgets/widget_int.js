// Test widget int class
casper.notebook_test(function () {
    var int_text = {};
    int_text.query = '.widget-area .widget-subarea .my-second-int-text input';
    int_text.index = this.append_cell(
        'from IPython.html import widgets\n' + 
        'from IPython.display import display, clear_output\n' +
        'int_widget = widgets.IntText()\n' +
        'display(int_widget)\n' + 
        'int_widget._dom_classes = ["my-second-int-text"]\n' + 
        'print(int_widget.model_id)\n');
    this.execute_cell_then(int_text.index, function(index){
        int_text.model_id = this.get_output_cell(index).text.trim();
    });

    // Wait for the widget to actually display.
    this.wait_for_element(int_text.index, int_text.query);

    // Continue with the tests.
    this.then(function() {
        this.test.assert(this.cell_element_exists(int_text.index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(int_text.index, int_text.query),
            'Widget int textbox exists.');

        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '1.05');
    });

    this.wait_for_widget(int_text);

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox value set.');
        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '123456789');
    });

    this.wait_for_widget(int_text);

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '123456789\n', 
            'Long int textbox value set (probably triggers throttling).');
        this.cell_element_function(int_text.index, int_text.query, 'val', ['']);
        this.sendKeys(int_text.query, '12hello');
    });

    this.wait_for_widget(int_text);

    index = this.append_cell('print(int_widget.value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '12\n', 
            'Invald int textbox value caught and filtered.');
    });

    var slider_query = '.widget-area .widget-subarea .slider';
    var int_text2 = {};
    int_text2.query = '.widget-area .widget-subarea .my-second-num-test-text input';
    int_text2.index = this.append_cell(
        'intrange = [widgets.BoundedIntTextWidget(),\n' +
        '    widgets.IntSliderWidget()]\n' +
        '[display(intrange[i]) for i in range(2)]\n' +
        'intrange[0]._dom_classes = ["my-second-num-test-text"]\n' +  
        'print(intrange[0].model_id)\n');
    this.execute_cell_then(int_text2.index, function(index){
        int_text2.model_id = this.get_output_cell(index).text.trim();
    });

    // Wait for the widgets to actually display.
    this.wait_for_element(int_text2.index, int_text2.query);
    this.wait_for_element(int_text2.index, slider_query);

    // Continue with the tests.
    this.then(function(){
        this.test.assert(this.cell_element_exists(int_text2.index, 
            '.widget-area .widget-subarea'),
            'Widget subarea exists.');

        this.test.assert(this.cell_element_exists(int_text2.index, slider_query),
            'Widget slider exists.');

        this.test.assert(this.cell_element_exists(int_text2.index, int_text2.query),
            'Widget int textbox exists.');
    });

    index = this.append_cell(
        'for widget in intrange:\n' +
        '    widget.max = 50\n' +
        '    widget.min = -50\n' +
        '    widget.value = 25\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){

        this.test.assertEquals(this.get_output_cell(index).text, 'Success\n', 
            'Int range properties cell executed with correct output.');

        this.test.assert(this.cell_element_exists(int_text2.index, slider_query), 
            'Widget slider exists.');

        this.test.assert(this.cell_element_function(int_text2.index, slider_query, 
            'slider', ['value']) == 25,
            'Slider set to Python value.');

        this.test.assert(this.cell_element_function(int_text2.index, int_text2.query,
            'val') == 25, 'Int textbox set to Python value.');

        // Clear the int textbox value and then set it to 1 by emulating
        // keyboard presses.
        this.evaluate(function(q){
            var textbox = IPython.notebook.element.find(q);
            textbox.val('1');
            textbox.trigger('keyup');
        }, {q: int_text2.query});
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '1\n', 
            'Int textbox set int range value');

        // Clear the int textbox value and then set it to 120 by emulating
        // keyboard presses.
        this.evaluate(function(q){
            var textbox = IPython.notebook.element.find(q);
            textbox.val('120');
            textbox.trigger('keyup');
        }, {q: int_text2.query});
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Int textbox value bound');

        // Clear the int textbox value and then set it to 'hello world' by 
        // emulating keyboard presses.  'hello world' should get filtered...
        this.evaluate(function(q){
            var textbox = IPython.notebook.element.find(q);
            textbox.val('hello world');
            textbox.trigger('keyup');
        }, {q: int_text2.query});
    });

    this.wait_for_widget(int_text2);

    index = this.append_cell('print(intrange[0].value)\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(this.get_output_cell(index).text, '50\n', 
            'Invalid int textbox characters ignored');
    });    

    index = this.append_cell(
        'a = widgets.IntSlider()\n' +
        'display(a)\n' +
        'a.max = -1\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(0, 0, 'Invalid int range max bound does not cause crash.');
    }, true); 

    index = this.append_cell(
        'a = widgets.IntSlider()\n' +
        'display(a)\n' +
        'a.min = 101\n' +
        'print("Success")\n');
    this.execute_cell_then(index, function(index){
        this.test.assertEquals(0, 0, 'Invalid int range min bound does not cause crash.');
    }, true);
});